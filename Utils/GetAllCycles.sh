find . -name "stats.txt" | sort | while read fname; do
  echo "$fname"
  cat $fname | grep "system.future_cpus0.numCycles"
done
