"""
Seed the database with realistic dummy data so the app has something to show.

Usage (from backend/, with the venv active):
    python seed.py

Safe to re-run: if the marker user (amelia_admin) already exists, it exits without
creating duplicates.
"""
import asyncio
import random
from datetime import UTC, datetime, timedelta

from auth import hash_password
from database import AsyncSessionLocal
from models import Comment, Like, Post, User
from sqlalchemy import select

USERS = [
    dict(username="maria_chef", email="maria@example.com", bio="cooking"),
    dict(username="devon_codes", email="devon@example.com", bio="tech"),
    dict(username="priya_travels", email="priya@example.com", bio="travel"),
    dict(username="alex_fitness", email="alex@example.com", bio="fitness"),
    dict(username="sophie_reads", email="sophie@example.com", bio="books"),
    dict(
        username="amelia_admin",
        email="admin@example.com",
        bio="admin",
        is_admin=True,
    ),
]
SEED_PASSWORD = "password123"

POSTS = [
    # (author username, title, content)
    (
        "maria_chef",
        "Five weeknight pasta dinners that actually work",
        "Weeknight cooking doesn't have to mean another sad bowl of plain noodles. "
        "This week I've been leaning on a garlicky lemon spaghetti that comes together "
        "in the time it takes the water to boil, plus a one-pan sausage and rapini orecchiette "
        "that dirties exactly one pot. The trick with all of these is starchy pasta water — "
        "save a mugful before you drain, and use it to loosen whatever sauce you're building. "
        "It emulsifies better than you'd expect and rescues a dish that looks too dry every single time.",
    ),
    (
        "maria_chef",
        "The one knife skill that changed my kitchen",
        "I spent years chopping onions the wrong way and didn't even know it. Learning the claw grip "
        "properly — knuckles forward, fingertips tucked, blade riding against the first knuckle — cut my "
        "prep time in half and, more importantly, stopped the near-misses. If you only fix one thing in "
        "your kitchen habits this year, make it this. Everything downstream gets faster and safer once "
        "your knife hand actually knows what it's doing.",
    ),
    (
        "maria_chef",
        "Why I finally bought a kitchen scale",
        "For years I measured flour by the cup and wondered why my bread came out different every time. "
        "A cup of flour can weigh anywhere from 120 to 150 grams depending on how it's scooped, which is a "
        "huge swing for a recipe that depends on hydration ratios. A ten-dollar scale fixed more of my baking "
        "problems than any amount of technique ever did.",
    ),
    (
        "devon_codes",
        "Why I stopped using global state in every React app",
        "Every project I started two years ago had Redux in it by default, whether it needed it or not. "
        "Most of what I was 'managing' was just server data with a cache-invalidation problem wearing a "
        "trench coat. Switching to colocated state plus a proper data-fetching layer removed about 40% of "
        "the boilerplate in my last project and made the remaining state actually mean something when you "
        "read it.",
    ),
    (
        "devon_codes",
        "A minimal mental model for async/await",
        "The thing that finally made async code click for me: an `async function` always returns a promise, "
        "full stop, even if you write `return 5`. Once that's automatic, `await` just reads as 'pause this "
        "function until that promise settles, and hand me the value.' Every confusing async bug I've debugged "
        "since then has come from someone, somewhere, forgetting that first rule.",
    ),
    (
        "devon_codes",
        "Postgres indexes: the ones I actually use",
        "Most days I reach for exactly two index types: a plain B-tree for equality and range lookups, and a "
        "GIN index when I'm filtering JSONB columns or doing full text search. Everything else — BRIN, hash, "
        "the exotic ones — I've needed maybe twice in production. Start boring, measure with EXPLAIN ANALYZE, "
        "and only reach for something exotic once the boring index provably isn't enough.",
    ),
    (
        "priya_travels",
        "Three days in Lisbon without a single tourist trap",
        "Skip the funicular line and just walk up through Alfama at golden hour instead — you'll get the same "
        "view over the rooftops without sharing it with forty other people. My favorite find was a tiny "
        "tasca near Graça that only had a chalkboard menu and the best grilled sardines I've had anywhere, "
        "including the coast. Lisbon rewards wandering more than almost any city I've been to.",
    ),
    (
        "priya_travels",
        "What nobody tells you about long-haul economy",
        "Compression socks are not a joke, and neither is getting up every ninety minutes whether you feel "
        "like it or not. The single biggest upgrade to how I feel after a 14-hour flight wasn't a neck pillow "
        "or noise-cancelling headphones — it was simply drinking twice as much water as felt necessary and "
        "skipping the free wine entirely.",
    ),
    (
        "priya_travels",
        "Packing list for two weeks, one carry-on",
        "The rule that actually works: lay out everything you think you need, then remove half of it. "
        "Merino wool base layers are doing more work than people realize — they don't hold odor, they pack "
        "small, and they work across a shocking range of temperatures. Once I switched to a capsule wardrobe "
        "built around three colors, I stopped checking bags entirely, even for month-long trips.",
    ),
    (
        "alex_fitness",
        "You probably don't need to train to failure",
        "Training to complete failure on every set sounds hardcore, but the research (and my own recovery "
        "tracking) says it mostly just digs a deeper fatigue hole without adding proportional muscle growth. "
        "Leaving one or two reps in the tank on most working sets lets you do more total quality volume across "
        "the week, which is what actually drives progress over months, not any single brutal set.",
    ),
    (
        "alex_fitness",
        "The warmup I do before every lower-body session",
        "Five minutes of easy cardio, then banded lateral walks, bodyweight Cossack squats, and a couple of "
        "light ramp-up sets on whatever the first lift is. That's it. It's boring and it works — my knees have "
        "felt dramatically better since I stopped skipping straight to the barbell.",
    ),
    (
        "sophie_reads",
        "Three quiet novels that stuck with me this year",
        "Not every good book needs a twist. The ones that have stayed with me longest this year were slow, "
        "close studies of ordinary people — a lighthouse keeper's diary of a single winter, a novel-in-letters "
        "between two sisters who never quite say what they mean. If you want a book that unfolds instead of "
        "explodes, these are the ones I keep recommending.",
    ),
    (
        "sophie_reads",
        "How I actually stuck to a reading habit",
        "The thing that worked wasn't a goal like '52 books a year' — it was putting the book on my pillow "
        "every morning when I made the bed, so it was physically in my way at night. Removing the two seconds "
        "of friction between 'wanting to read' and 'book in hand' did more than any tracking app ever did.",
    ),
    (
        "amelia_admin",
        "Welcome to FastAPI Blogger",
        "This is a small community blog built on FastAPI and React, where anyone can write posts, leave "
        "comments, and follow what people are working on. Say hello, write your first post, and don't be a "
        "stranger. Looking forward to seeing what everyone shares here.",
    ),
]

COMMENTS = [
    "This is such a helpful breakdown, thank you for writing it up.",
    "I've been doing this wrong for years apparently — trying your suggestion today.",
    "Completely agree, this matches my experience almost exactly.",
    "Do you have a follow-up post planned? Would love to hear more about this.",
    "Saved this one, coming back to it later.",
    "Interesting take — I've had the opposite experience though.",
    "This finally explains something that's been bugging me for weeks.",
    "Great write-up, short and to the point.",
]

REPLIES = [
    "Glad it helped!",
    "Let me know how it goes for you.",
    "Yeah, that's fair — curious what led to the opposite experience for you.",
    "Might write a follow-up soon, thanks for the nudge.",
]


async def main():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.username == "amelia_admin"))
        if existing.scalars().first():
            print("Seed data already present (amelia_admin exists) — skipping.")
            return

        users_by_username = {}
        for u in USERS:
            user = User(
                username=u["username"],
                email=u["email"],
                password_hash=hash_password(SEED_PASSWORD),
                is_admin=u.get("is_admin", False),
            )
            db.add(user)
            users_by_username[u["username"]] = user
        await db.flush()

        now = datetime.now(UTC)
        posts = []
        for i, (author_username, title, content) in enumerate(POSTS):
            post = Post(
                title=title,
                content=content,
                user_id=users_by_username[author_username].id,
                date_posted=now - timedelta(days=len(POSTS) - i, hours=random.randint(0, 12)),
            )
            db.add(post)
            posts.append(post)
        await db.flush()

        all_users = list(users_by_username.values())

        for post in posts:
            other_users = [u for u in all_users if u.id != post.user_id]

            # scattered likes, weighted so posts don't all look identical
            likers = random.sample(other_users, k=random.randint(1, len(other_users)))
            for liker in likers:
                db.add(Like(user_id=liker.id, post_id=post.id))

            # a couple of top-level comments, sometimes with a reply
            commenters = random.sample(other_users, k=random.randint(1, 3))
            for commenter in commenters:
                comment = Comment(
                    content=random.choice(COMMENTS),
                    user_id=commenter.id,
                    post_id=post.id,
                    date_posted=post.date_posted + timedelta(hours=random.randint(1, 48)),
                )
                db.add(comment)
                await db.flush()

                if random.random() < 0.5:
                    replier = random.choice([u for u in all_users if u.id != commenter.id])
                    db.add(
                        Comment(
                            content=random.choice(REPLIES),
                            user_id=replier.id,
                            post_id=post.id,
                            parent_id=comment.id,
                            date_posted=comment.date_posted + timedelta(hours=random.randint(1, 24)),
                        )
                    )

        await db.commit()
        print(f"Seeded {len(USERS)} users and {len(posts)} posts with comments/replies/likes.")
        print(f"All seed users share the password: {SEED_PASSWORD}")
        print("Admin login: admin@example.com")


if __name__ == "__main__":
    asyncio.run(main())
