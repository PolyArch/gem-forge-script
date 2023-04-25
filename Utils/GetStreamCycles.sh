find . -name "stream.stats.*.txt" | sort | while read fname; do
  echo "$fname"
  cat $fname | grep "numCycle " | head -n 1
done
