#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

parallelism=3

for size in 16 32 64 128 160 320;do
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
          # iterations=$(( 100 * size * size / range ))
          # if [[ ${iterations} -gt 256000 ]];then
          #   iterations=256000
          # fi
          likely_convergence_time=$(( (size/range) * (size/range) * 16 ))
          num_print_intervals=256
          print_interval=$(( likely_convergence_time / num_print_intervals ))
          while [[ $(jobs|wc -l) -gt ${parallelism} ]];do
            sleep 1
          done
          logfile="output/mira_${size}x${size}_r${range}_d${domain}.log"
          date > "${logfile}"
          echo "size: ${size} range: ${range} domain: ${domain}" >> "${logfile}"
          /usr/bin/time -avo "${logfile}" -- python run.py -f mira_${size}x${size}.pgm -r ${range} -d ${domain} -p ${print_interval} -v 2 >> "${logfile}" 2>&1 && date >> "${logfile}" || date >> "${logfile}" &

        fi
      done
    fi
  done
done
exit 0
