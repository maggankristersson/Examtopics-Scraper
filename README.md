Prerequisites:

<code>pip3 install -r requirements.txt</code>

Arguments:

  <code>-h, --help</code>            show this help message and exit


  <code>-t TEST, --test TEST</code>  (Required) Test name to scrape questions for

 
  <code>-c COUNT, --count COUNT</code> (Optional) Number of questions to scrape ("max" is default)

  
  <code>-k KEYWORDS, --keywords KEYWORDS</code> (Optional) Keywords to filter questions (comma-separated)

  
  <code>-d, --debug</code>           Enable debug mode

        Examples:
          scraper.py -t 350-401 -c 10 -k HSRP,VRF
          scraper.py -t 300-410 -c max -k BGP,OSPF,DMVPN

Notes:
      - Press <code>'q'</code>   at any time to stop the scraping process and generate the HTML file with the results gathered so far.
      


 
