wait=600

# cd Software/server/sync
rm -rf exact.csv polling.csv
touch exact.csv polling.csv
timeout $wait python3 test_sync.py & timeout $wait python3 external_sync.py
python3 avg_sync.py