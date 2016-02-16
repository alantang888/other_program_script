import futures;
import subprocess;
import logging;
import time;

# Setting
EXPECT_SCRIPT = "./changePasswdExpectScript.exp";
CONCURRENT_THREAD=10;
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', filename = "result.txt");

# declare variable
userName = "";
oldUserPasswd = "";
oldRootPasswd = "";
newUserPasswd = "";
newRootPasswd = "";

def callExpectChangePasswd(serverIP):
    startTime = time.time();
    # call expect script to change password.
    proc = subprocess.Popen([EXPECT_SCRIPT, serverIP, userName, oldUserPasswd, oldRootPasswd, newUserPasswd, newRootPasswd], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    out, err = proc.communicate()
    runTime = time.time() - startTime;
    if proc.returncode == 0:
        logging.info("{} OK, spend {} seconds.".format(serverIP, runTime));
    else:
        logging.warning("{} got problem, message: {}, spend {} seconds.".format(serverIP, err.strip(), runTime));
    return None;

if __name__ == "__main__":
    # Ask user information
    serverListPath = raw_input("Server list location: ").strip();
    userName = raw_input("User name: ").strip();
    oldUserPasswd = raw_input("Old user passwd: ").strip();
    oldRootPasswd = raw_input("Old root passwd: ").strip();
    newUserPasswd = raw_input("New user passwd: ").strip();
    newRootPasswd = raw_input("New root passwd: ").strip();
    
    # read server list file
    tempServerList = [];
    try:
        with open(serverListPath, "r") as reader:
            tempServerList = reader.readlines();
    except:
        print "Read server list error.";
    serverList = [server for server in [rawServer.strip() for rawServer in tempServerList] if server != ""];
    
    # start process
    logging.info("Process start.")
    logging.debug("Got list: '{}'".format("', '".join(serverList)))
    
    with futures.ThreadPoolExecutor(max_workers=CONCURRENT_THREAD) as executor:
        result = executor.map(callExpectChangePasswd, serverList);
        for r in result:
            pass;
    logging.info("Process end.")