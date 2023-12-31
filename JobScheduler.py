
import datetime
import multiprocessing
import multiprocessing.dummy
import logging
import unittest
import tempfile
import time
import traceback
import threading
import sys


def error(msg, *args):
    print(msg)
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.WARNING)
    logger.error(msg, *args)


class LogExceptions(object):
    def __init__(self, callable, log_fn=None, timeout=None):
        self.__callable = callable
        self.__timeout = timeout
        self.__log_fn = log_fn

    def __call__(self, *args, **kwargs):
        # Redirect to log f.
        if self.__log_fn is not None:
            log_f = open(self.__log_fn, "w")
            sys.stdout = log_f
            sys.stderr = log_f
        pool = multiprocessing.dummy.Pool(1)
        result = pool.apply_async(self.__callable, args=args, kwds=kwargs)
        try:
            out = result.get(self.__timeout)
        except multiprocessing.TimeoutError as e:
            pool.terminate()
            raise e
        except Exception as e:
            error(traceback.format_exc())
            # Reraise the original exception so the Pool worker can clean up
            raise ValueError('Job Failed.')
        else:
            return out


class JobScheduler:
    """
    A job scheduler.
    Since we use pool class, which use a queue.Queue to pass tasks to the worker
    processes. Everything that goes through queue.Queue must be picklable.
    Pickle is a serialization protocol for python. ONLY TOP-LEVEL object can be
    pickled!
    This means only top-level function for the job, and no nested class object for
    the parameter.
    """
    STATE_INIT = 1
    STATE_READY = 2
    STATE_STARTED = 3
    STATE_FINISHED = 4
    STATE_FAILED = 5
    STATE_TIMEOUTED = STATE_FAILED + 1

    class Job:
        def __init__(self, job_id, name, job, args, timeout=None):
            self.job_id = job_id
            self.name = name
            self.job = job
            self.args = args
            self.status = JobScheduler.STATE_INIT
            self.timeout = timeout
            self.start_time = datetime.datetime.now()
            self.end_time = datetime.datetime.now()
            self.log_fn = None

    def __init__(self, name, cores, poll_seconds, log_dir=None):
        self.state = JobScheduler.STATE_INIT
        self.name = name
        self.cores = cores
        self.poll_seconds = poll_seconds
        self.log_dir = log_dir
        self.current_job_id = 1
        self.lock = multiprocessing.Lock()
        self.pool = multiprocessing.Pool(processes=self.cores)
        self.jobs = dict()
        self.job_children = dict()
        self.job_deps = dict()
        self.running_jobs = 0
        self.ready_jobs = list()

        # Remember the common name within jobs.
        self.common_job_name = None

        multiprocessing.log_to_stderr()

    # Add a job and set the dependence graph.
    def add_job(self, name, job, args, deps, timeout=None):
        assert(self.state == JobScheduler.STATE_INIT)
        new_job_id = self.current_job_id
        self.current_job_id += 1
        self.job_deps[new_job_id] = list(deps)
        for dep in deps:
            assert(dep in self.jobs)
            self.job_children[dep].append(new_job_id)
        self.job_children[new_job_id] = list()
        self.jobs[new_job_id] = self.Job(new_job_id, name, job, args, timeout)
        return new_job_id

    # Caller should hold the locker.
    def kick(self, job_id):
        assert(job_id in self.jobs)
        job = self.jobs[job_id]
        if job.status != JobScheduler.STATE_INIT:
            return
        ready = True
        for dep in self.job_deps[job_id]:
            if self.jobs[dep].status != JobScheduler.STATE_FINISHED:
                ready = False
                break
        if ready:
            job.status = JobScheduler.STATE_READY
            self.ready_jobs.append(job)

    def call_back(self, job_id):
        """
        Callback when the job is done.
        Caller should not hold the lock.
        """
        print('{job} finished'.format(job=job_id))
        self.lock.acquire()
        assert(job_id in self.jobs)
        job = self.jobs[job_id]
        assert(job.status == JobScheduler.STATE_STARTED)
        job.status = JobScheduler.STATE_FINISHED
        job.end_time = datetime.datetime.now()
        for child in self.job_children[job_id]:
            child_job = self.jobs[child]
            assert(child_job.status == JobScheduler.STATE_INIT or child_job.status ==
                   JobScheduler.STATE_FAILED)
            self.kick(child)
        self.dump(sys.stdout)
        self.dump(self.log_f)
        self.running_jobs -= 1
        self.lock.release()

    def failed(self, job_id):
        """
        Mark the job and all its descent job Failed.
        Caller should not hold the lock.
        """
        self.lock.acquire()
        assert(job_id in self.jobs)
        job = self.jobs[job_id]
        assert(job.res.ready() and (not job.res.successful()))
        assert(job.status == JobScheduler.STATE_STARTED)

        # Try to get the exception.
        new_status = JobScheduler.STATE_FAILED
        try:
            job.res.get(timeout=1)
        except multiprocessing.TimeoutError:
            # This is a timeout error.
            new_status = JobScheduler.STATE_TIMEOUTED
        except Exception as e:
            # Normal failed job.
            print(e)
            new_status = JobScheduler.STATE_FAILED
        else:
            print("Should reraise an exception for unsuccessful job.")
            assert(False)

        job.status = new_status
        job.end_time = datetime.datetime.now()
        stack = list()
        for child_id in self.job_children[job_id]:
            stack.append(job_id)
        while stack:
            job_id = stack.pop()
            print('{job} unsucceeded'.format(job=job_id))
            job = self.jobs[job_id]
            job.status = JobScheduler.STATE_FAILED
            for child_id in self.job_children[job_id]:
                stack.append(child_id)
        self.dump(sys.stdout)
        self.dump(self.log_f)
        self.dump_failed(self.log_failed_f)
        self.running_jobs -= 1
        self.lock.release()

    def start_ready_jobs(self):
        # Caller should hold the lock.
        started = 0
        while self.running_jobs < self.cores and self.ready_jobs:
            job = self.ready_jobs[0]
            self.ready_jobs.pop(0)
            self.running_jobs += 1
            # Create a log file for the job.
            if self.log_dir is not None:
                with tempfile.NamedTemporaryFile(
                    mode='wt',
                    dir=self.log_dir,
                    prefix='job_log.',
                    # suffix='.log',
                    delete=False,
                    ) as f:
                    job.log_fn = f.name

            # Do we actually need to use nested lambda to capture job_id?
            job.status = JobScheduler.STATE_STARTED
            job.start_time = datetime.datetime.now()
            started += 1

            print('{job} started'.format(job=job.job_id))
            job.res = self.pool.apply_async(
                func=LogExceptions(job.job, job.log_fn, job.timeout),
                args=job.args,
                callback=(lambda i: lambda _: self.call_back(i))(job.job_id)
            )
        if started > 0:
            self.dump(sys.stdout)
            self.dump(self.log_f)

    def str_status(self, job):
        status = job.status
        msg = 'INIT'
        diff = None
        if status == JobScheduler.STATE_INIT:
            msg = 'INIT'
        elif status == JobScheduler.STATE_TIMEOUTED:
            msg = 'TIMEOUTED'
        elif status == JobScheduler.STATE_READY:
            msg = 'READY'
        elif status == JobScheduler.STATE_FAILED:
            diff = job.end_time - job.start_time
            msg = 'FAILED'
        elif status == JobScheduler.STATE_STARTED:
            diff = datetime.datetime.now() - job.start_time
            msg = 'STARTED'
        elif status == JobScheduler.STATE_FINISHED:
            diff = job.end_time - job.start_time
            msg = 'FINISHED'
        log_fn = ''
        if job.log_fn is not None:
            log_fn = f'{job.log_fn} '
        diff_str = ''
        if diff is not None:
            diff_str = f'{datetime.timedelta(days=diff.days, seconds=diff.seconds)} '
        return f'{log_fn}{diff_str}{msg}'

    def dump(self, f):
        stack = list()
        for job_id in self.jobs:
            if len(self.job_deps[job_id]) == 0:
                stack.append((job_id, 0))
        f.write('=================== Job Scheduler =====================\n')
        f.write(f'!! Common Job Name $ = {self.common_job_name}\n')
        while stack:
            job_id, level = stack.pop()
            job = self.jobs[job_id]
            f.write('{tab}{job_id:3} {job_name} {status}\n'.format(
                tab='  '*level,
                job_id=job_id,
                job_name=self.compress_job_name(job.name),
                status=self.str_status(self.jobs[job_id])
            ))
            for child_id in self.job_children[job_id]:
                stack.append((child_id, level + 1))
        f.write(f'!! Common Job Name $ = {self.common_job_name}\n')
        f.write('=================== Job Scheduler =====================\n')
        f.flush()

    def dump_failed(self, f):
        # Only write the failed job.
        stack = list()
        for job_id in self.jobs:
            if len(self.job_deps[job_id]) == 0:
                stack.append((job_id, 0))
        f.write('=================== Job Scheduler =====================\n')
        f.write(f'!! Common Job Name $ = {self.common_job_name}\n')
        while stack:
            job_id, level = stack.pop()
            job = self.jobs[job_id]
            status = self.jobs[job_id].status
            if status > JobScheduler.STATE_STARTED and status != JobScheduler.STATE_FINISHED:
                f.write('{tab}{job_id} {job_name} {status}\n'.format(
                    tab='  '*level,
                    job_id=job_id,
                    job_name=self.compress_job_name(job.name),
                    status=self.str_status(self.jobs[job_id])
                ))
            for child_id in self.job_children[job_id]:
                stack.append((child_id, level + 1))
        f.write(f'!! Common Job Name $ = {self.common_job_name}\n')
        f.write('=================== Job Scheduler =====================\n')
        f.flush()

    def run(self):
        assert(self.state == JobScheduler.STATE_INIT)
        self.find_common_job_name()
        self.log_f = tempfile.NamedTemporaryFile(
            mode='wt', prefix='job_scheduler.', suffix='.{n}'.format(n=self.name), delete=False)
        self.log_failed_f = tempfile.NamedTemporaryFile(
            mode='wt', prefix='job_scheduler.', suffix='.{n}.fail'.format(n=self.name), delete=False)
        print(self.log_f.name)
        seconds = 0
        
        # Initial dump.
        self.dump(sys.stdout)
        self.dump(self.log_f)

        self.state = JobScheduler.STATE_STARTED
        self.lock.acquire()
        for job_id in self.job_deps:
            self.kick(job_id)
        self.start_ready_jobs()
        self.lock.release()
        # Poll every n seconds.
        while True:
            time.sleep(self.poll_seconds)

            seconds += self.poll_seconds
            if seconds > 600:
                seconds = 0
                self.log_f.truncate()
                self.dump(sys.stdout)
                self.dump(self.log_f)
                self.dump_failed(self.log_failed_f)

            finished = True
            # Try to get the res.
            for job_id in self.jobs:
                job = self.jobs[job_id]
                if job.status == JobScheduler.STATE_STARTED:
                    if job.res.ready() and (not job.res.successful()):
                        self.failed(job_id)

            self.lock.acquire()
            self.start_ready_jobs()
            for job_id in self.jobs:
                job = self.jobs[job_id]
                if job.status < JobScheduler.STATE_FINISHED:
                    finished = False
                    break
            self.lock.release()
            if finished:
                self.state = JobScheduler.STATE_FINISHED
                break
        self.dump(sys.stdout)
        self.dump(self.log_f)
        self.dump_failed(self.log_failed_f)

        self.pool.close()
        self.log_f.close()
        self.log_failed_f.close()
        self.pool.join()

    def find_common_job_name(self):
        N = len(self.jobs)
        if N < 1:
            return
        job_names = list()
        for job_id in self.jobs:
            job = self.jobs[job_id]
            job_names.append(job.name)
        
        min_len = min([len(x) for x in job_names])

        max_common_name = ''

        first_job_name = job_names[0]
        first_len = len(first_job_name)
        for lhs in range(first_len):
            for rhs in range(first_len, lhs, -1):
                sub = first_job_name[lhs:rhs]

                all_have = True
                for remain_job_name in job_names[1:]:
                    if remain_job_name.find(sub) == -1:
                        all_have = False
                        break
                
                if all_have:
                    common_len = rhs - lhs
                    if common_len > len(max_common_name):
                        max_common_name = sub
                    # No need to search for smaller rhs.
                    break

        if max_common_name != '':
            self.common_job_name = max_common_name

    def compress_job_name(self, job_name):
        if self.common_job_name is None:
            return job_name
        lhs = job_name.find(self.common_job_name)
        assert(lhs != -1)
        rhs = lhs + len(self.common_job_name)
        return f'{job_name[:lhs]}${job_name[rhs:]}'


def test_job(id):
    print('job {job} executed'.format(job=id))


def test_job_fail(id):
    print('job {job} failed'.format(job=id))
    raise ValueError('Job deliberately failed.')


def test_job_fail_bash(id):
    print('job {job} failed in bash'.format(job=id))
    import subprocess
    print('job {job} failed in bash'.format(job=id))
    subprocess.check_call(['false'])


def test_job_timeout(id, seconds):
    print('job {job} sleeps {s} seconds.'.format(job=id, s=seconds))
    time.sleep(5)


class TestJobScheduler(unittest.TestCase):

    # Test all jobs are finished.
    # python unittest framework will treat test_* functions as unit test.
    # So make this helper function as assert_*
    def assert_all_jobs_status(self, scheduler, status):
        for job_id in scheduler.jobs:
            job = scheduler.jobs[job_id]
            self.assertEqual(
                job.status, status, 'There is job {job} with wrong status.'.format(job=job_id))

    def assert_job_status(self, scheduler, status, job_id):
        job = scheduler.jobs[job_id]
        self.assertEqual(
            job.status, status, 'There is job {job} with wrong status.'.format(job=job_id))

    # Simple test case to test linear dependence.
    def test_linear(self):
        scheduler = JobScheduler('test', 4, 1)
        deps = []
        for i in range(8):
            new_job_id = scheduler.add_job('test_job', test_job, (i,), deps)
            deps = list()
            deps.append(new_job_id)
        scheduler.run()
        self.assert_all_jobs_status(scheduler, JobScheduler.STATE_FINISHED)
        self.assertEqual(scheduler.state, JobScheduler.STATE_FINISHED)

    # Simple linear dependence when everything failed.
    def test_linear_fail(self):
        scheduler = JobScheduler('test', 4, 1)
        deps = []
        for i in range(8):
            new_job_id = scheduler.add_job(
                'test_job_fail', test_job_fail, (i,), deps)
            deps = list()
            deps.append(new_job_id)
        scheduler.run()
        self.assert_all_jobs_status(scheduler, JobScheduler.STATE_FAILED)
        self.assertEqual(scheduler.state, JobScheduler.STATE_FINISHED)

    # Simple linear dependence when the middle one failed in bash.
    def test_linear_fail_bash(self):
        scheduler = JobScheduler('test', 4, 1)
        deps = []
        job_ids = list()
        failed_id = 0
        for i in range(8):
            if i == 4:
                new_job_id = scheduler.add_job(
                    'test_job_fail_bash', test_job_fail_bash, (i,), deps)
                failed_id = new_job_id
            else:
                new_job_id = scheduler.add_job(
                    'test_job', test_job, (i,), deps)
            job_ids.append(new_job_id)
            deps = list()
            deps.append(new_job_id)
        scheduler.run()
        for i in job_ids:
            if i >= failed_id:
                self.assert_job_status(scheduler, JobScheduler.STATE_FAILED, i)
            else:
                self.assert_job_status(
                    scheduler, JobScheduler.STATE_FINISHED, i)
        self.assertEqual(scheduler.state, JobScheduler.STATE_FINISHED)

    def test_timeout_basic(self):
        scheduler = JobScheduler('test', 4, 1)
        scheduler.add_job(
            'test_job_timeout', test_job_timeout, (0, 5), list(), timeout=1)
        scheduler.run()
        self.assert_all_jobs_status(scheduler, JobScheduler.STATE_TIMEOUTED)

    def test_thread_not_quit(self):
        scheduler = JobScheduler('test', 4, 1)
        for i in range(8):
            scheduler.add_job(
                'test_job_fail_bash', test_job_fail_bash, (i,), list())
        for i in range(8, 16):
            scheduler.add_job(
                'test_job', test_job, (i,), list())
        scheduler.run()
        # Job id starts from 1.
        for i in range(1, 9):
            self.assert_job_status(scheduler, JobScheduler.STATE_FAILED, i)
        for i in range(9, 17):
            self.assert_job_status(scheduler, JobScheduler.STATE_FINISHED, i)

    def test_massive_jobs(self):
        scheduler = JobScheduler('test', 4, 1)
        n_jobs = 1000
        # The first 4 jobs are 30 second timeout
        for i in range(4):
            scheduler.add_job(
                'test_job_timeout', test_job_timeout, (i, 30), list())
        # Push in the rest jobs.
        for i in range(5, n_jobs):
            scheduler.add_job(
                'test_job', test_job, (i,), list())
        scheduler.run()
        self.assert_all_jobs_status(scheduler, JobScheduler.STATE_FINISHED)


if __name__ == '__main__':
    unittest.main()
