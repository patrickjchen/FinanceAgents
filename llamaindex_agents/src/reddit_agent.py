import asyncpraw
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from shared_lib.schemas import MCPRequest, MCPResponse
from shared_lib.monitor import MonitorAgent

class RedditAgent:
    def __init__(self):
        self.monitor = MonitorAgent()
        # Note: Reddit client will be initialized in async methods

    async def _get_reddit_client(self):
        """Get AsyncPRAW Reddit client"""
        return asyncpraw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="FinanceAgents-LlamaIndex/1.0"
        )

    async def _get_recent_posts(self, query: str, since: datetime = None) -> List:
        """Fetch recent posts from Reddit based on query"""
        reddit = None
        try:
            if since is None:
                since = datetime.utcnow() - timedelta(days=30)

            reddit = await self._get_reddit_client()
            subreddit = await reddit.subreddit("stocks")

            posts = []
            async for post in subreddit.search(query, sort="new", time_filter="month", limit=10):
                post_time = datetime.utcfromtimestamp(post.created_utc)
                if post_time >= since:
                    posts.append(post)
                if len(posts) >= 3:
                    break
            return posts
        except Exception as e:
            print(f"[RedditAgent] Error fetching posts for '{query}': {e}")
            return []
        finally:
            if reddit:
                await reddit.close()


    async def _get_comments(self, post) -> List[str]:
        try:
            await post.comments.replace_more(limit=0)
            comments = []
            async for comment in post.comments:
                if len(comments) >= 10:
                    break
                if hasattr(comment, 'body'):
                    comments.append(comment.body)
            return comments
        except Exception as e:
            print(f"[RedditAgent] Error fetching comments: {e}")
            return []

    def _summarize_comment(self, comment: str) -> str:
        return comment[:100] + ("..." if len(comment) > 100 else "")

    def _analyze_sentiment(self, comment: str) -> float:
        import random
        return random.uniform(-1, 1)

    def _summarize_post(self, post) -> str:
        return (post.selftext[:200] + ("..." if len(post.selftext) > 200 else "")) if hasattr(post, 'selftext') else ""

    async def run(self, request: MCPRequest) -> MCPResponse:
        """Process Reddit sentiment analysis query"""
        start_time = datetime.now()
        companies = request.context.companies
        user_query = request.context.user_query
        posts_data = []
        status = "processing"
        try:
            since = datetime.utcnow() - timedelta(days=30)
            if companies:
                for company in companies:
                    company_posts = await self._get_recent_posts(company, since)
                    # Filter posts to ensure company name is in title or selftext
                    filtered_posts = [
                        post for post in company_posts
                        if company.lower() in post.title.lower() or company.lower() in getattr(post, 'selftext', '').lower()
                    ]
                    if not filtered_posts:
                        continue
                    company_posts_data = []
                    for post in filtered_posts:
                        comments = await self._get_comments(post)
                        comment_summaries = [self._summarize_comment(c) for c in comments]
                        sentiment_scores = [self._analyze_sentiment(c) for c in comments]
                        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                        company_posts_data.append({
                            "post_title": post.title,
                            "post_url": post.url,
                            "summary": self._summarize_post(post),
                            "comment_summaries": comment_summaries,
                            "avg_sentiment": avg_sentiment
                        })
                    posts_data.append({
                        "company": company,
                        "posts": company_posts_data
                    })
            else:
                relevant_posts = await self._get_recent_posts(user_query, since)
                relevant_posts_data = []
                for post in relevant_posts:
                    comments = await self._get_comments(post)
                    comment_summaries = [self._summarize_comment(c) for c in comments]
                    sentiment_scores = [self._analyze_sentiment(c) for c in comments]
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                    relevant_posts_data.append({
                        "post_title": post.title,
                        "post_url": post.url,
                        "summary": self._summarize_post(post),
                        "comment_summaries": comment_summaries,
                        "avg_sentiment": avg_sentiment
                    })
                posts_data.append({
                    "company": None,
                    "posts": relevant_posts_data
                })
            status = "success"
        except Exception as e:
            status = "failed"
            posts_data = {"error": str(e)}
        completed_time = datetime.now()
        response_json = {
            "agent": "RedditAgent",
            "started_timestamp": start_time.isoformat(),
            "companies": companies,
            "response": posts_data,
            "completed_timestamp": completed_time.isoformat(),
            "status": status
        }
        try:
            with open("monitor_logs.json", "a") as f:
                f.write(json.dumps(response_json) + "\n")
        except Exception as e:
            pass
        return MCPResponse(
            request_id=request.request_id,
            data={"reddit": posts_data},
            context_updates={"last_reddit_access": completed_time.isoformat()},
            status=status
        )

