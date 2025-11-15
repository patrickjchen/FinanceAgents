from fastapi import BackgroundTasks
from mcp.schemas import MCPRequest, MCPResponse
import praw
from datetime import datetime, timedelta
from typing import List, Optional
import json
import random
import os

class RedditAgent:
    def __init__(self):
        
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="webapp"
        )
        self.subreddit = self.reddit.subreddit("stocks")

    async def run(self, request: MCPRequest, bg: BackgroundTasks) -> MCPResponse:
        start_time = datetime.now()
        companies = request.context.companies
        user_query = request.context.user_query
        posts_data = []
        status = "processing"
        try:
            since = datetime.utcnow() - timedelta(days=30)
            print(f"[RedditAgent] Companies: {companies}, Query: {user_query}")
            if companies:
                for company in companies:
                    print(f"[RedditAgent] Searching posts for company: {company}")
                    company_posts = self._get_recent_posts(company, since)
                    # Filter posts to ensure company name is in title or selftext
                    filtered_posts = [
                        post for post in company_posts
                        if company.lower() in post.title.lower() or company.lower() in getattr(post, 'selftext', '').lower()
                    ]
                    print(f"[RedditAgent] Found {len(filtered_posts)} filtered posts for {company}")
                    if not filtered_posts:
                        print(f"there is no topics about this {company}.")
                        continue
                    company_posts_data = []
                    for post in filtered_posts:
                        comments = self._get_comments(post)
                        print(f"[RedditAgent] Post '{post.title}' has {len(comments)} comments")
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
                print(f"[RedditAgent] No companies found, searching for query: {user_query}")
                relevant_posts = self._get_recent_posts(user_query, since)
                print(f"[RedditAgent] Found {len(relevant_posts)} posts for query '{user_query}'")
                relevant_posts_data = []
                for post in relevant_posts:
                    comments = self._get_comments(post)
                    print(f"[RedditAgent] Post '{post.title}' has {len(comments)} comments")
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
            print(f"[RedditAgent] Exception: {e}")
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
            print(f"[RedditAgent] Logging error: {e}")
        return MCPResponse(
            request_id=request.request_id,
            data={"reddit": posts_data},
            context_updates={"last_reddit_access": completed_time.isoformat()},
            status=status
        )

    def _get_recent_posts(self, query: str, since: datetime) -> List:
        try:
            print(f"[RedditAgent] _get_recent_posts: Searching for '{query}' since {since}")
            posts = []
            for post in self.subreddit.search(query, sort="new", time_filter="month"):
                post_time = datetime.utcfromtimestamp(post.created_utc)
                if post_time >= since:
                    posts.append(post)
                if len(posts) >= 3:
                    break
            print(f"[RedditAgent] _get_recent_posts: Returning {len(posts)} posts for '{query}'")
            return posts
        except Exception as e:
            print(f"[RedditAgent] Error fetching posts for '{query}': {e}")
            return []

    def _get_comments(self, post) -> List[str]:
        try:
            post.comments.replace_more(limit=0)
            comments = [c.body for c in post.comments[:10]]
            print(f"[RedditAgent] _get_comments: Got {len(comments)} comments for post '{getattr(post, 'title', '')}'")
            return comments
        except Exception as e:
            print(f"[RedditAgent] Error fetching comments: {e}")
            return []

    def _summarize_comment(self, comment: str) -> str:
        return comment[:100] + ("..." if len(comment) > 100 else "")

    def _analyze_sentiment(self, comment: str) -> float:
        return random.uniform(-1, 1)

    def _summarize_post(self, post) -> str:
        return (post.selftext[:200] + ("..." if len(post.selftext) > 200 else "")) if hasattr(post, 'selftext') else ""

    def get_llm_prompt(self, topics):
        return (
            "You are a social media sentiment analyst. Given the following Reddit topics and their sentiment scores, "
            "summarize the main topics, their sentiment (positive/negative/neutral), and why these topics are trending. "
            "Make the summary user-friendly and informative.\n\n" +
            f"Topics: {json.dumps(topics, ensure_ascii=False)}"
        )