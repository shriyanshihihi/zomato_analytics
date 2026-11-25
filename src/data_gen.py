"""Synthetic data generator.

WHAT / WHY (read this first)
  The real data is not available, so this file INVENTS a small food-delivery dataset so every
  other file can run. It is the "raw tables" box of the architecture. Nothing here is a CV claim;
  it only makes the claims demonstrable.
  How a user is simulated, month by month (Jan-Sep 2025):
    1. pick a segment (casual / regular / power) -> how many orders per month they place
    2. place orders (cuisine, time of day, value, delivery fee, discount)
    3. decide whether they stay active (more orders -> more likely to stay)
    4. decide whether they buy Gold (more orders, fee-sensitive, explorer -> more likely)
    5. Gold members order more, pay no delivery fee, and renew more if they use it
  Because these rules are written by us, the analysis later "finds" them. That proves the
  PIPELINE works; it does NOT prove anything about real customers.

!!! ALL DATA PRODUCED HERE IS SYNTHETIC DEMO DATA. It is NOT real Zomato data. !!!
It exists only so the SQL / cohort / affinity / simulation pipeline can run end to end.
Behavioural effects (e.g. frequent orderers convert to Gold more often) are built into
the generator as assumptions, so findings on this data validate the PIPELINE, not the real world.

Tables produced
  users          (user_id, signup_date, city, channel)
  orders         (order_id, user_id, order_date, cuisine, daypart, order_value,
                  delivery_fee, discount_amt, is_gold_order)
  subscriptions  (sub_id, user_id, start_date, end_date, is_renewal_term, renewed_next)
                 one row per 3-month Gold TERM; renewed_next is NULL while undecided.
"""
import calendar
from datetime import date

import numpy as np
import pandas as pd

CUISINES = ["North Indian", "Biryani", "Chinese", "Pizza", "Burgers",
            "South Indian", "Desserts", "Healthy", "Rolls", "Beverages"]
CUISINE_W = np.array([.22, .18, .12, .10, .09, .08, .07, .05, .05, .04])
CUISINE_W = CUISINE_W / CUISINE_W.sum()
DAYPARTS = ["breakfast", "lunch", "snack", "dinner", "late_night"]
DAYPART_W = np.array([.07, .28, .15, .38, .12])
CITIES = ["Delhi NCR", "Mumbai", "Bengaluru", "Hyderabad", "Pune", "Kolkata"]
CHANNELS = ["organic", "paid_ads", "referral", "partner_offer"]

# segment: (share of users, mean orders per month, mean order value in INR)
SEGMENTS = {"casual": (0.50, 1.3, 380), "regular": (0.35, 3.0, 450), "power": (0.15, 5.5, 520)}
MONTHS = pd.period_range("2025-01", "2025-09", freq="M")
GOLD_TERM_MONTHS = 3


def _month_bounds(p):
    return date(p.year, p.month, 1), date(p.year, p.month, p.days_in_month)


def generate(n_users=4000, seed=42):
    rng = np.random.default_rng(seed)
    seg_names = list(SEGMENTS)
    seg_p = [SEGMENTS[s][0] for s in seg_names]
    users, orders, subs = [], [], []
    oid = sid = 0

    for uid in range(1, n_users + 1):
        p0 = MONTHS[rng.integers(0, 9)]                    # signup Jan..Sep
        signup = date(p0.year, p0.month, int(rng.integers(1, p0.days_in_month + 1)))
        users.append((uid, signup.isoformat(), rng.choice(CITIES), rng.choice(CHANNELS)))

        seg = rng.choice(seg_names, p=seg_p)
        _, base_lam, aov = SEGMENTS[seg]
        fee_sensitive = rng.random() < 0.35                 # hidden trait, not in tables
        explorer = rng.random() < 0.25                      # likes trying cuisines
        night_owl = rng.random() < 0.20
        discount_lover = rng.random() < 0.30
        fav = rng.choice(CUISINES, p=CUISINE_W)

        active, gold_until, term_orders, term_start, is_renewal = True, None, 0, None, 0
        for m_idx, p in enumerate(MONTHS):
            if p < p0:
                continue
            m_start, m_end = _month_bounds(p)
            is_gold = gold_until is not None and p <= gold_until
            n = 0
            if active:
                d0 = signup.day if p == p0 else 1
                frac = (p.days_in_month - d0 + 1) / p.days_in_month
                lam = base_lam * frac * ((1.5 if fee_sensitive else 1.25) if is_gold else 1.0)
                n = int(rng.poisson(lam))
                for _ in range(n):
                    oid += 1
                    day = int(rng.integers(d0, p.days_in_month + 1))
                    if explorer and rng.random() < 0.55:
                        cuisine = rng.choice(CUISINES)
                    else:
                        cuisine = fav if rng.random() < 0.6 else rng.choice(CUISINES, p=CUISINE_W)
                    dp_w = DAYPART_W.copy()
                    if night_owl:
                        dp_w[4] *= 4
                    daypart = rng.choice(DAYPARTS, p=dp_w / dp_w.sum())
                    value = float(rng.lognormal(np.log(aov), 0.35)) * (1.08 if is_gold else 1.0)
                    fee = 0.0 if is_gold else float(rng.choice([30, 40, 50, 60]))
                    disc = value * float(rng.uniform(.10, .30)) if (discount_lover and rng.random() < .7) else 0.0
                    orders.append((oid, uid, date(p.year, p.month, day).isoformat(), cuisine, daypart,
                                   round(value, 2), fee, round(disc, 2), int(is_gold)))
                # churn decision: more orders this month -> more likely to stay
                p_stay = min(0.97, 0.45 + 0.08 * min(n, 5) + (0.08 if is_gold else 0))
                if rng.random() > p_stay:
                    active = False
            if is_gold:
                term_orders += n
                if p == gold_until:                         # term ends -> renew or lapse
                    avg = term_orders / GOLD_TERM_MONTHS
                    renew = rng.random() < min(0.9, 0.30 + 0.12 * min(avg, 4))
                    subs.append((sid, uid, term_start.isoformat(), m_end.isoformat(), is_renewal, int(renew)))
                    if renew:
                        sid += 1
                        gold_until = gold_until + GOLD_TERM_MONTHS
                        term_start, is_renewal, term_orders = date(m_end.year + (m_end.month == 12), m_end.month % 12 + 1, 1), 1, 0
                    else:
                        gold_until = None
                    continue
            elif active and n > 0 and m_idx < len(MONTHS) - 1:
                # Gold conversion decision at month end (starts 1st of next month)
                p_conv = 0.008 + 0.010 * min(n, 6)
                if fee_sensitive and n >= 3:
                    p_conv += 0.05
                if explorer:
                    p_conv += 0.015
                if rng.random() < p_conv:
                    sid += 1
                    gold_until = p + GOLD_TERM_MONTHS
                    term_start = date(m_end.year + (m_end.month == 12), m_end.month % 12 + 1, 1)
                    is_renewal, term_orders = 0, 0
        # term still running (or undecided) at data cutoff
        if gold_until is not None and gold_until > MONTHS[-1]:
            end = _month_bounds(gold_until)[1]
            subs.append((sid, uid, term_start.isoformat(), end.isoformat(), is_renewal, None))

    users_df = pd.DataFrame(users, columns=["user_id", "signup_date", "city", "channel"])
    orders_df = pd.DataFrame(orders, columns=["order_id", "user_id", "order_date", "cuisine", "daypart",
                                              "order_value", "delivery_fee", "discount_amt", "is_gold_order"])
    subs_df = pd.DataFrame(subs, columns=["sub_id", "user_id", "start_date", "end_date",
                                          "is_renewal_term", "renewed_next"])
    subs_df["sub_id"] = range(1, len(subs_df) + 1)
    return users_df, orders_df, subs_df
