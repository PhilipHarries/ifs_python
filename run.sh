#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

parallelism=5

for size in 16 64 128 160 320;do
  for range in 2 4 8 16 32;do
    if [[ ${range} -ge ${size} ]];then
      continue
    else
      for domain in 4 8 16 32 64 128;do
        if [[ ${range} -ge ${domain} ]];then
          continue
        elif [[ ${domain} -ge ${size} ]];then
          continue
        else
          iterations=$(( 100 * size * size / range ))
          if [[ ${iterations} -gt 256000 ]];then
            iterations=256000
          fi
          num_print_intervals=$(( iterations / 64 ))
          while [[ $(jobs|wc -l) -gt ${parallelism} ]];do
            sleep 1
          done
          logfile="output/mira_${size}x${size}_r${range}_d${domain}.log"
          date > "${logfile}"
          echo "size: ${size} range: ${range} domain: ${domain} iterations: ${iterations}" >> "${logfile}"
          /usr/bin/time -avo "${logfile}" -- python run.py -f mira_${size}x${size}.pgm -r ${range} -d ${domain} -i ${iterations} -p ${num_print_intervals} >> "${logfile}" 2>&1 &
          date >> "${logfile}"

        fi
      done
    fi
  done
done
exit 0
