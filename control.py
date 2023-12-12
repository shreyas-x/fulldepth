from fulldepth import FullDepth
import time

t = FullDepth(com='COM9', addr=b'\x00')
print("Please enter RPM: ", end="")
rpm = int(input())

count = 10

t.sendRPM(int(rpm/3))
time.sleep(0.1)
t.sendRPM(int(2*rpm/3))
time.sleep(0.1)

init = time.time()
while (count > 0):
    # t.ADR_THRUSTER = b'\x00'
    t.sendRPM(rpm)
    time.sleep(0.1)
    # t.SER.read_all()
    reply = t.askForData(inst="rpm")
    # response = []
    # for _ in range(7):
    #     response.append(t.SER.read())
    
    # print(t.parseData(response, query="rpm"))
    print(f"Read RPM as {reply}")
    time.sleep(0.1)

    count -= 1
print(f"Runtime: {time.time() - init:.2f}")

# t.ADR_THRUSTER = b'\x00'
t.stopThruster()