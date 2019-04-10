#!/usr/bin/env python
import os,sys,argparse,logging,time
import getpass

parser = argparse.ArgumentParser()
parser.add_argument("brokeraddr",type=str,help="Broker Address")
parser.add_argument("-l","--logfile",type=str, default=None,
                    help="where the log file is writen to")
parser.add_argument("-d","--debug",action="store_true",
                    help="set logger level to debug")
parser.add_argument("-w","--weights-dir",type=str,default=None,
                    help="directory where weights can be found")
parser.add_argument("-m","--mode",type=str,default="cuda",
                    help="run with device. either 'cuda' or 'cpu'")
parser.add_argument("-b","--batch-size",type=int,default=1,
                    help="batch size for each worker")
parser.add_argument("-t","--ssh-tunnel",type=str,default=None,
                    help="Tunnel using SSH through the given IP address")
parser.add_argument("-u","--ssh-user",type=str,default=None,
                    help="username for ssh tunnel command")

if __name__ == "__main__":

    args = parser.parse_args(sys.argv[1:])

    from start_dense_ublarflow_worker import startup_dense_ublarflow_worker


    level = logging.INFO
    if args.debug:
        level = logging.DEBUG

    if args.logfile is not None:
        logging.basicConfig(filename=args.logfile,level=level)

    log = logging.getLogger("start_denselarflow_worker_main")
    logging.basicConfig(level=logging.INFO)

    weights_dir = "../ublarcvserver/networks/larflow/weights/"
    if args.weights_dir is not None:
        weights_dir = args.weights_dir
    weights_files = {"y2u":weights_dir+"/devfiltered_larflow_y2u_832x512_32inplanes.tar",
                     "y2v":weights_dir+"/devfiltered_larflow_y2v_832x512_32inplanes.tar"}

    for p in xrange(2):
        if not os.path.exists(weights_files[p]):
            log.error("did not find weight file at: "+weights_files[p])
            sys.exit(1)

    endpoint   = args.brokeraddr
    batch_size = args.batch_size

    if args.ssh_tunnel is not None:
        if args.ssh_user is None:
            raise ValueError("If using ssh tunnel, must provide user")
        print "Using ssh, please provide password"
        ssh_password =  getpass.getpass()
        ssh_url = "%s@%s"%(args.ssh_user,args.ssh_tunnel)
    else:
        ssh_url = None
        ssh_password = None

    workers_v = {}
    log.info("starting the workers")
    for flowdir in ['y2u','y2v']:
        pworker = start_daemon_ublarflow_worker(endpoint,flowdir,
                                                weights_files[flowdir],
                                                device,batch_size,False,ssh_url,ssh_password)
        workers_v[flowdir] = pworker


    log.info("Workers started")
    nalive = 2
    while nalive==2:
        time.sleep(60)
        nalive = 0
        for flowdir in ['y2u','y2v']:
            if workers_v[flowdir].is_alive():
                nalive+=1
    log.info("At least one worker stopped")

