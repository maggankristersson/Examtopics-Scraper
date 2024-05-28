Prerequisites:

<code>pip3 install -r requirements.txt</code>

optional arguments:

  <code>-h, --help</code>            show this help message and exit

 
  <code>-c COUNT, --count COUNT</code> Number of questions to scrape (or "max" for all)

  
  <code>-t TEST, --test TEST</code>  Test name to scrape questions for

  
  <code>-k KEYWORDS, --keywords KEYWORDS</code> Keywords to filter questions (comma-separated)

  
  <code>-d, --debug</code>           Enable debug mode

        Examples:
          scraper.py -c 10 -t 350-401 -k BGP,OSPF,RIP
          scraper.py -c max -t 350-401 -k BGP

Notes:
      - Press <code>'q'</code>   at any time to stop the scraping process and generate the HTML file with the results gathered so far.
      


 
