lines = open(r'e:\NetworkMonitor\network-engine\qa_test.py', encoding='utf-8').read().splitlines()
for i in range(236, 246):
    print(i + 1, '|', lines[i])