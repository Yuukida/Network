for all parts:
-only the socket library is used
-Do not redirect the entire browser to the proxy as the browser will send requests that are not html or http, and may cause the server to crash
-Please use Firefox as the browser
-the socket takes a few second to process to make sure nothing is sent from the web server/client, please be patient and wait until the ip and port   number is displayed to access another site
-if the server is stuck, please press ctrl + c to continue
-Make sure nothing is open except the browser and the terminal
-Sometimes the browser will have bugs that send a different request to the server or unable to connect to server while the user is still typing the url,  please restart the server in that case
-if you wish to shut down the server, please close the command prompt
-an ide would work better than command prompt running the files as the cmd is more buggy and slow

Part A:
-After running the server in command prompt, an ip will be printed in the terminal, use that ip as the server ip and use 4000 as its port
-the initial URL would then be (printed ip):4000/
-make sure the html requested is in the same folder as the py file.
-type in (printed ip):4000/(html file) in the browser to access the html file
-if it's an invalid html, the server will return 404
-you can repeat the process again if you wish


Part B:
-clear browser cache before doing any of the steps, especially when the website is already cached in the browser through proxy as the browser might load  its own cache and disconnect with the server prematurely
-the socket takes a few second to process to make sure nothing is sent from the web server/client, please be patient and wait until the ip and port    number is displayed to access another site or the terminal has stopped outputing
-After running the file in command prompt, a ip will be printed in the terminal, use that ip as the server ip and use 4001 as its port
-the initial URL would then be (printed ip):4001/(the website main page url)
-enter the url to the browser, the terminal should print what is received from the client and what is recevied from the web server as well as the web  site url
-if the website has been cached, the terminal would print what is sent from the cache
-if it's an invalid website, the server will return 404
-if you are trying to test 404 not found, make sure the url is not connectable, as most urls can be conneccted using a socket even though they dont  respond
-for www.google.com or other larger sites, sometimes the server will not have enough time to cache/response/send as the message may take a long time to send/receive or due to server lag, as such, new requests might appear when the website is accessed again through the proxy
-the proxy server caches each sub requests from a website as separate txt files with the sub directory as their name
--"/" in url are replaced with ".-.-.-." to aovid duplicate urls.
-if the server is stuck on reciving, please press ctrl + c to continue
-you can repeat the process again if you wish

working site:
-www.google.com (with www., just google.com returns 301, images may or may not show up
-example.org (html
-http://www.cs.toronto.edu/~ylzhang/static/img/photo.png (a png file, working
-www.owgr.com (loads the html but there will be too much img requests for the server to handle, so if you do test with this site, please be patient and  wait for the server to finishes. This website also takes a long time to load
-amazon.com (sends 301 and otehr https servers alike

