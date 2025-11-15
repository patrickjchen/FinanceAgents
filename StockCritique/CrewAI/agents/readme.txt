Here are all agents:
1.RouterAgent: analyze the user's query and control which agents to provide info based on whether is a fincance question, public company names, mapping to tickers, ...
2.GeneralAgent: connect openAI to handle non-financial questions as a writer and sicitise
3.FinanceAgent: create lightRAG for internal docs(non public info) and summary of the relevance content to user
4.YahooAgent: get the tickers of public companies from RouterAgent, then extract last 30 days daily stock prices and statistics data to user
5.Reddit_agent: get sentimentality of stock market from Reddit social media
6.SECAgent: connet SEC API to retrieve relevance info to users
7.MonitorAgent: get all health status from each agent with timestamp
......


