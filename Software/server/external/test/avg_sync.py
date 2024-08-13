import csv

def compare():
    exact = [ [float(line[0]), int(line[1])] for line in csv.reader(open("exact.csv"))]
    polling = [ [float(line[0]), int(line[1])]  for line in csv.reader(open("polling.csv"))]

    del exact[0]

    totalError = 0
    count = 0
    for i in range(min(len(exact), len(polling))):
        if exact[i][1] == polling[i][1]:
            totalError += abs(exact[i][0] - polling[i][0]) if exact[i][0] < polling[i][0] else 0
            count += 1
            print(f"Exact: {exact[i][1]}, Polling: {polling[i][1]}, i: {i}")
    
    return totalError / count

if __name__ == "__main__":
    print(compare())
    