import subprocess
import json
import argparse

# Endpoint della SMF (sostituiscilo con quello reale)
SMF_BASE_URL = "http://192.168.70.133:8080/nsmf_event-exposure/v1/subscriptions"

# Token OAuth2 fornito dall'ambiente di rete 5GC
#TOKEN = "YOUR_ACCESS_TOKEN" -->no token needed in OAI 5gCN

# Dati della sottoscrizione
payload = {
  "notifId": "notifSMF",
  "notifUri": "https://172.17.0.1/callbacks/volume",
  "ImmeRep": True,
  "expiry": "2025-11-27T10:45:00Z",
  "notifMethod": "PERIODIC",
  "repPeriod": 30,
  "eventSubs":[
        { "event": "QOS_MON",           
          "ueIpAddr": {"ipv4Addr": "12.1.1.2"},
          "upfEvents": [
            {                     
            "type": "QOS_MONITORING",
            "immediateFlag": True,
            "measurementTypes": ["VOLUME_MEASUREMENT"],                   
            "granularityOfMeasurement": "PER_SESSION" 
            }                      
          ]     
        }                                              
  ]    
}

def parse_cli():
    parser = argparse.ArgumentParser(
        description="Parse HTTP request parameters for SMF from command line."
    )

    parser.add_argument(
        "-X", "--method",
        type=str,
        default="POST",
        help="HTTP method to use (GET, POST, PUT, DELETE, ...)"
    )

    parser.add_argument(
        "-I", "--subId",
        type=str,
        help="Target Subscription Id in SMF"
    )

    parser.add_argument(
        "-v", "--http-version",
        type=int,
        choices=[1,2],
        default=1,
        help="HTTP version to use"
    )

    parser.add_argument(
        "-d", "--data",
        type=str,
        default=payload,
        help="Json payload to send to SMF"
    )

    return parser.parse_args()

def make_http_request(url, httpversion=1, method="GET",data=None): 
    valid_methods = ["GET", "POST", "PUT", "DELETE"]
    method = method.upper()

    if method not in valid_methods:
        raise ValueError(f"Invalid method '{method}'. Must be one of {valid_methods}")   
    if httpversion==1:
        cmd=[
            "curl",
             "-v", 
            f"-X{method}",
            #"-s",                         # Silent mode (no progress)
            url
            ]
    if httpversion==2: 
        cmd=[
            "curl",
             "-v", 
            f"-X{method}",
            #"-s",                         # Silent mode (no progress)
            "--http2-prior-knowledge",  # Force HTTP/2 cleartext
            url
            ]
    if data:
        if isinstance(data, str):
            data = json.loads(data)  # Parse string to dict if needed
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
          
    # Run curl with --http2-prior-knowledge to force HTTP/2 cleartext (h2c)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    print(result.stderr)
    if result.returncode != 0:
        print(f"Curl command failed! Code: {result.returncode}")
        print(result.stdout)
        return None

    try:
        data = json.loads(result.stdout)
        print(json.dumps(data, indent=2))
        return data
    except json.JSONDecodeError:
        print("Response was not valid JSON:")
        print(result.stdout)
        return result.stdout


if __name__ == "__main__":
    args = parse_cli()
    if args.method=="PUT":                                                        #PUT not yet implemented in SMF    
      SMF_URL=SMF_BASE_URL+"/"+args.subId
      make_http_request(SMF_URL,args.http_version, "PUT", args.data)
    if args.method=="POST":
      make_http_request(SMF_BASE_URL,args.http_version, "POST", args.data)
    else:
      make_http_request(SMF_BASE_URL,args.http_version, args.method, args.data)  #GET and DELETE not implemented in OAI SMF 
