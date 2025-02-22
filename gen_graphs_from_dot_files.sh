#!/bin/bash

#STR_ARRAY=("string1" "string2" "string3")
STR_ARRAY=("main" "PostgresSingleUserMain" "BootstrapModeMain" "GucInfoMain" "SubPostmasterMain" "PostmasterMain" "PostgresMain" "WalWriterMain" "BackgroundWriterMain" "CheckpointerMain" "AutoVacWorkerMain" "ParallelQueryMain" "WalSummarizerMain" "BackgroundWorkerMain" "AutoVacLauncherMain" "SysLoggerMain" "BackendMain" "PgArchiverMain" "WalReceiverMain" "StartupProcessMain" "CheckerModeMain")

for ITEM in "${STR_ARRAY[@]}"; do
  echo "current: ${ITEM}"
  dot -Tsvg "${ITEM}".dot -o "${ITEM}.svg"
done