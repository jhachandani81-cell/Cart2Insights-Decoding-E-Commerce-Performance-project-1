import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_CONFIG = {
    "host": "localhost",
    "database": "ecommerce_db",
    "user": "postgres",
    "password": "alok",
    "port": "5432"
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# RUN SQL QUERY SAFELY
# ============================================================

@st.cache_data(ttl=300)
def run_query(query, params=None):

    conn = None

    try:

        conn = get_connection()

        # Avoid transaction problems
        conn.autocommit = True

        df = pd.read_sql_query(
            query,
            conn,
            params=params
        )

        return df

    except Exception as e:

        st.error(f"Database Error: {e}")

        return pd.DataFrame()

    finally:

        if conn is not None:
            conn.close()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🛒 E-Commerce Dashboard")

st.sidebar.markdown(
    """
    ### Dashboard Sections

    - 📊 Business Overview
    - 💰 Sales Analysis
    - 👥 Customer Analysis
    - 🏪 Seller & Product Analysis
    - 🚚 Delivery Analysis
    - ⭐ Customer Experience
    """
)

st.sidebar.markdown("---")


# ============================================================
# TEST DATABASE CONNECTION
# ============================================================

try:

    test_conn = get_connection()
    test_conn.close()

    st.sidebar.success("Database Connected")

except Exception as e:

    st.sidebar.error("Database Connection Failed")

    st.error(
        f"""
        Could not connect to PostgreSQL.

        Check:

        1. PostgreSQL is running
        2. Database name is correct
        3. Username is correct
        4. Password is correct
        5. Port is correct

        Error:
        {e}
        """
    )

    st.stop()


# ============================================================
# TITLE
# ============================================================

st.title("🛒 E-Commerce Sales & Customer Analytics Dashboard")

st.markdown(
    """
    **Interactive SQL-powered dashboard**

    This dashboard analyzes sales, customers, sellers,
    products, delivery performance and customer reviews.
    """
)




st.sidebar.header("🔎 Filters")




category_query = """
SELECT DISTINCT
    COALESCE(product_category_name_english, 'Unknown') AS category
FROM order_items
ORDER BY category;
"""

category_df = run_query(category_query)

if not category_df.empty:

    category_list = category_df["category"].dropna().tolist()

else:

    category_list = []


selected_categories = st.sidebar.multiselect(
    "Product Category",
    category_list
)



state_query = """
SELECT DISTINCT customer_state
FROM customers
ORDER BY customer_state;
"""

state_df = run_query(state_query)

if not state_df.empty:

    state_list = state_df["customer_state"].dropna().tolist()

else:

    state_list = []


selected_states = st.sidebar.multiselect(
    "Customer State",
    state_list
)




status_query = """
SELECT DISTINCT order_status
FROM orders
ORDER BY order_status;
"""

status_df = run_query(status_query)

if not status_df.empty:

    status_list = status_df["order_status"].dropna().tolist()

else:

    status_list = []


selected_status = st.sidebar.multiselect(
    "Order Status",
    status_list
)




conditions = []
params = []


if selected_categories:

    placeholders = ",".join(
        ["%s"] * len(selected_categories)
    )

    conditions.append(
        f"oi.product_category_name_english IN ({placeholders})"
    )

    params.extend(selected_categories)


if selected_states:

    placeholders = ",".join(
        ["%s"] * len(selected_states)
    )

    conditions.append(
        f"c.customer_state IN ({placeholders})"
    )

    params.extend(selected_states)


if selected_status:

    placeholders = ",".join(
        ["%s"] * len(selected_status)
    )

    conditions.append(
        f"o.order_status IN ({placeholders})"
    )

    params.extend(selected_status)


if conditions:

    filter_condition = " AND ".join(conditions)

else:

    filter_condition = "1=1"


st.header("📊 1. Business Overview")


overview_query = f"""
WITH order_revenue AS
(
    SELECT
        o.order_id,
        COALESCE(
            SUM(
                COALESCE(
                    oi.item_total_value,
                    oi.price + oi.freight_value
                )
            ),
            0
        ) AS order_value
    FROM orders o
    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id
    LEFT JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE {filter_condition}
    GROUP BY o.order_id
)

SELECT

    COALESCE(SUM(order_value), 0) AS total_revenue,

    COUNT(order_id) AS total_orders,

    (
        SELECT COUNT(DISTINCT customer_id)
        FROM orders
    ) AS total_customers,

    (
        SELECT COUNT(*)
        FROM sellers
    ) AS total_sellers,

    ROUND(
        COALESCE(AVG(order_value), 0),
        2
    ) AS average_order_value,

    (
        SELECT ROUND(
            AVG(review_score)::numeric,
            2
        )
        FROM order_reviews
    ) AS average_review_score

FROM order_revenue;
"""


overview = run_query(
    overview_query,
    params
)


if not overview.empty:

    total_revenue = float(
        overview.iloc[0]["total_revenue"] or 0
    )

    total_orders = int(
        overview.iloc[0]["total_orders"] or 0
    )

    total_customers = int(
        overview.iloc[0]["total_customers"] or 0
    )

    total_sellers = int(
        overview.iloc[0]["total_sellers"] or 0
    )

    average_order_value = float(
        overview.iloc[0]["average_order_value"] or 0
    )

    average_review_score = float(
        overview.iloc[0]["average_review_score"] or 0
    )

else:

    total_revenue = 0
    total_orders = 0
    total_customers = 0
    total_sellers = 0
    average_order_value = 0
    average_review_score = 0


# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "💰 Total Revenue",
        f"₹{total_revenue:,.2f}"
    )

with col2:

    st.metric(
        "📦 Total Orders",
        f"{total_orders:,}"
    )

with col3:

    st.metric(
        "👥 Total Customers",
        f"{total_customers:,}"
    )


col4, col5, col6 = st.columns(3)

with col4:

    st.metric(
        "🏪 Total Sellers",
        f"{total_sellers:,}"
    )

with col5:

    st.metric(
        "🧾 Average Order Value",
        f"₹{average_order_value:,.2f}"
    )

with col6:

    st.metric(
        "⭐ Average Review Score",
        f"{average_review_score:.2f}/5"
    )

# ============================================================
# SALES ANALYSIS
# ============================================================

st.header("💰 2. Sales Analysis")


# ============================================================
# MONTHLY REVENUE
# ============================================================

monthly_query = f"""
SELECT

    DATE_TRUNC(
        'month',
        o.order_purchase_timestamp
    ) AS month,

    ROUND(
        SUM(
            COALESCE(
                oi.item_total_value,
                oi.price + oi.freight_value
            )
        )::numeric,
        2
    ) AS revenue,

    COUNT(DISTINCT o.order_id) AS orders

FROM orders o

JOIN order_items oi
    ON o.order_id = oi.order_id

JOIN customers c
    ON o.customer_id = c.customer_id

WHERE {filter_condition}

GROUP BY month

ORDER BY month;
"""


monthly_df = run_query(
    monthly_query,
    params
)


if not monthly_df.empty:

    monthly_df["month"] = pd.to_datetime(
        monthly_df["month"]
    )

    st.subheader("📈 Monthly Revenue Trend")

    fig = px.line(
        monthly_df,
        x="month",
        y="revenue",
        markers=True,
        title="Monthly Revenue Trend"
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Revenue",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# REVENUE BY CATEGORY
# ============================================================

category_revenue_query = f"""
SELECT

    COALESCE(
        oi.product_category_name_english,
        'Unknown'
    ) AS category,

    ROUND(
        SUM(
            COALESCE(
                oi.item_total_value,
                oi.price + oi.freight_value
            )
        )::numeric,
        2
    ) AS revenue,

    COUNT(DISTINCT oi.order_id) AS orders

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN customers c
    ON o.customer_id = c.customer_id

WHERE {filter_condition}

GROUP BY category

HAVING SUM(
    COALESCE(
        oi.item_total_value,
        oi.price + oi.freight_value
    )
) > 0

ORDER BY revenue DESC
LIMIT 15;
"""


category_revenue_df = run_query(
    category_revenue_query,
    params
)


if not category_revenue_df.empty:

    st.subheader("🏷️ Revenue by Category")

    fig = px.bar(
        category_revenue_df,
        x="revenue",
        y="category",
        orientation="h",
        title="Top 15 Categories by Revenue",
        text_auto=".2s"
    )

    fig.update_layout(
        yaxis=dict(
            categoryorder="total ascending"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# TOP SELLING PRODUCTS
# ============================================================

top_product_query = f"""
SELECT

    oi.product_id,

    COUNT(*) AS items_sold,

    COUNT(DISTINCT oi.order_id) AS orders,

    ROUND(
        SUM(
            COALESCE(
                oi.item_total_value,
                oi.price + oi.freight_value
            )
        )::numeric,
        2
    ) AS revenue

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN customers c
    ON o.customer_id = c.customer_id

WHERE {filter_condition}

GROUP BY oi.product_id

ORDER BY revenue DESC

LIMIT 15;
"""


top_product_df = run_query(
    top_product_query,
    params
)


if not top_product_df.empty:

    st.subheader("📦 Top-Selling Products")

    fig = px.bar(
        top_product_df,
        x="revenue",
        y="product_id",
        orientation="h",
        color="items_sold",
        title="Top Products by Revenue"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# SALES BY LOCATION
# ============================================================

location_query = f"""
SELECT

    c.customer_state,

    COUNT(DISTINCT o.order_id) AS orders,

    ROUND(
        SUM(
            COALESCE(
                oi.item_total_value,
                oi.price + oi.freight_value
            )
        )::numeric,
        2
    ) AS revenue

FROM customers c

JOIN orders o
    ON c.customer_id = o.customer_id

JOIN order_items oi
    ON o.order_id = oi.order_id

WHERE {filter_condition}

GROUP BY c.customer_state

ORDER BY revenue DESC;
"""


location_df = run_query(
    location_query,
    params
)


if not location_df.empty:

    st.subheader("🗺️ Sales by Customer State")

    fig = px.bar(
        location_df,
        x="customer_state",
        y="revenue",
        title="Revenue by State",
        text_auto=".2s"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# CUSTOMER ANALYSIS
# ============================================================

st.header("👥 3. Customer Analysis")


# ============================================================
# CUSTOMER DISTRIBUTION
# ============================================================

customer_distribution_query = """

SELECT

    customer_state,

    COUNT(*) AS customers

FROM customers

GROUP BY customer_state

ORDER BY customers DESC;

"""


customer_distribution_df = run_query(
    customer_distribution_query
)


if not customer_distribution_df.empty:

    st.subheader("👥 Customer Distribution")

    fig = px.pie(
        customer_distribution_df,
        names="customer_state",
        values="customers",
        title="Customer Distribution by State"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# CUSTOMER SPENDING
# ============================================================

customer_spending_query = f"""
SELECT

    c.customer_unique_id,

    COUNT(DISTINCT o.order_id) AS order_count,

    ROUND(
        SUM(
            COALESCE(
                oi.item_total_value,
                oi.price + oi.freight_value
            )
        )::numeric,
        2
    ) AS total_spending

FROM customers c

JOIN orders o
    ON c.customer_id = o.customer_id

JOIN order_items oi
    ON o.order_id = oi.order_id

WHERE {filter_condition}

GROUP BY c.customer_unique_id

ORDER BY total_spending DESC

LIMIT 20;
"""


customer_spending_df = run_query(
    customer_spending_query,
    params
)


if not customer_spending_df.empty:

    st.subheader("💳 Top Customers by Spending")

    fig = px.bar(
        customer_spending_df,
        x="total_spending",
        y="customer_unique_id",
        orientation="h",
        color="order_count",
        title="Top 20 Customers by Spending"
    )

    fig.update_layout(
        yaxis=dict(
            categoryorder="total ascending"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# REPEAT VS NEW CUSTOMERS
# ============================================================

repeat_customer_query = """

WITH customer_orders AS
(
    SELECT

        c.customer_unique_id,

        COUNT(DISTINCT o.order_id) AS order_count

    FROM customers c

    JOIN orders o
        ON c.customer_id = o.customer_id

    GROUP BY c.customer_unique_id
)

SELECT

    CASE

        WHEN order_count = 1
        THEN 'New Customer'

        ELSE 'Repeat Customer'

    END AS customer_type,

    COUNT(*) AS customers

FROM customer_orders

GROUP BY customer_type;

"""


repeat_customer_df = run_query(
    repeat_customer_query
)


if not repeat_customer_df.empty:

    st.subheader("🔁 New vs Repeat Customers")

    fig = px.pie(
        repeat_customer_df,
        names="customer_type",
        values="customers",
        hole=0.45,
        title="Customer Type Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# SELLER ANALYSIS
# ============================================================

st.header("🏪 4. Seller & Product Analysis")


seller_query = f"""
SELECT

    s.seller_id,

    s.seller_state,

    COUNT(DISTINCT oi.order_id) AS orders,

    ROUND(
        SUM(
            COALESCE(
                oi.item_total_value,
                oi.price + oi.freight_value
            )
        )::numeric,
        2
    ) AS revenue

FROM sellers s

JOIN order_items oi
    ON s.seller_id = oi.seller_id

JOIN orders o
    ON oi.order_id = o.order_id

JOIN customers c
    ON o.customer_id = c.customer_id

WHERE {filter_condition}

GROUP BY

    s.seller_id,
    s.seller_state

ORDER BY revenue DESC

LIMIT 15;
"""


seller_df = run_query(
    seller_query,
    params
)


if not seller_df.empty:

    st.subheader("🏆 Top Sellers")

    fig = px.bar(
        seller_df,
        x="revenue",
        y="seller_id",
        orientation="h",
        color="orders",
        title="Top Sellers by Revenue"
    )

    fig.update_layout(
        yaxis=dict(
            categoryorder="total ascending"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# SELLER REVENUE VS ORDERS
# ============================================================

if not seller_df.empty:

    st.subheader("📊 Seller Revenue vs Number of Orders")

    fig = px.scatter(
        seller_df,
        x="orders",
        y="revenue",
        size="revenue",
        hover_name="seller_id",
        color="seller_state",
        title="Seller Performance"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# PRODUCT CATEGORY PERFORMANCE
# ============================================================

product_performance_query = """

SELECT

    COALESCE(
        oi.product_category_name_english,
        'Unknown'
    ) AS category,

    COUNT(*) AS items_sold,

    ROUND(
        AVG(oi.price)::numeric,
        2
    ) AS average_price,

    ROUND(
        SUM(
            COALESCE(
                oi.item_total_value,
                oi.price + oi.freight_value
            )
        )::numeric,
        2
    ) AS revenue

FROM order_items oi

GROUP BY category

ORDER BY revenue DESC

LIMIT 20;

"""


product_performance_df = run_query(
    product_performance_query
)


if not product_performance_df.empty:

    st.subheader("📦 Product Category Performance")

    fig = px.scatter(
        product_performance_df,
        x="items_sold",
        y="revenue",
        size="revenue",
        color="average_price",
        hover_name="category",
        title="Category Sales Volume vs Revenue"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# DELIVERY ANALYSIS
# ============================================================

st.header("🚚 5. Delivery Analysis")


# ============================================================
# DELIVERY PERFORMANCE
# ============================================================

delivery_query = f"""
WITH delivery_data AS
(
    SELECT

        o.order_id,

        o.order_purchase_timestamp,

        o.order_delivered_customer_date,

        o.order_estimated_delivery_date,

        EXTRACT(
            DAY FROM
            (
                o.order_delivered_customer_date
                -
                o.order_purchase_timestamp
            )
        ) AS delivery_days,

        CASE

            WHEN
                o.order_delivered_customer_date
                <=
                o.order_estimated_delivery_date

            THEN 'On Time'

            ELSE 'Delayed'

        END AS delivery_status

    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    WHERE

        o.order_delivered_customer_date IS NOT NULL

        AND {filter_condition}
)

SELECT

    delivery_status,

    COUNT(*) AS orders,

    ROUND(
        AVG(delivery_days)::numeric,
        2
    ) AS average_delivery_days

FROM delivery_data

GROUP BY delivery_status;

"""


delivery_df = run_query(
    delivery_query,
    params
)


if not delivery_df.empty:

    col1, col2 = st.columns(2)

    with col1:

        fig = px.pie(
            delivery_df,
            names="delivery_status",
            values="orders",
            hole=0.45,
            title="On-Time vs Delayed Orders"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        fig = px.bar(
            delivery_df,
            x="delivery_status",
            y="average_delivery_days",
            title="Average Delivery Days"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# DELIVERY PERFORMANCE BY LOCATION
# ============================================================

delivery_location_query = """

WITH delivery_status AS
(
    SELECT

        c.customer_state,

        CASE

            WHEN
                o.order_delivered_customer_date
                <=
                o.order_estimated_delivery_date

            THEN 'On Time'

            ELSE 'Delayed'

        END AS delivery_status

    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    WHERE
        o.order_delivered_customer_date IS NOT NULL
)

SELECT

    customer_state,

    COUNT(*) AS total_orders,

    SUM(
        CASE
            WHEN delivery_status = 'On Time'
            THEN 1
            ELSE 0
        END
    ) AS on_time_orders,

    SUM(
        CASE
            WHEN delivery_status = 'Delayed'
            THEN 1
            ELSE 0
        END
    ) AS delayed_orders

FROM delivery_status

GROUP BY customer_state

ORDER BY delayed_orders DESC;

"""


delivery_location_df = run_query(
    delivery_location_query
)


if not delivery_location_df.empty:

    st.subheader("📍 Delivery Performance by State")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=delivery_location_df["customer_state"],
            y=delivery_location_df["on_time_orders"],
            name="On Time"
        )
    )

    fig.add_trace(
        go.Bar(
            x=delivery_location_df["customer_state"],
            y=delivery_location_df["delayed_orders"],
            name="Delayed"
        )
    )

    fig.update_layout(
        barmode="group",
        title="On-Time vs Delayed Orders by State",
        xaxis_title="State",
        yaxis_title="Number of Orders"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# DELIVERY DELAY VS REVIEW SCORE
# ============================================================

delay_review_query = """

WITH delivery_status AS
(
    SELECT

        o.order_id,

        CASE

            WHEN
                o.order_delivered_customer_date
                <=
                o.order_estimated_delivery_date

            THEN 'On Time'

            ELSE 'Delayed'

        END AS delivery_status

    FROM orders o

    WHERE
        o.order_delivered_customer_date IS NOT NULL
)

SELECT

    d.delivery_status,

    ROUND(
        AVG(r.review_score)::numeric,
        2
    ) AS average_review_score,

    COUNT(*) AS reviews

FROM delivery_status d

JOIN order_reviews r
    ON d.order_id = r.order_id

GROUP BY d.delivery_status

ORDER BY average_review_score DESC;

"""


delay_review_df = run_query(
    delay_review_query
)


if not delay_review_df.empty:

    st.subheader("⭐ Delivery Status vs Review Score")

    fig = px.bar(
        delay_review_df,
        x="delivery_status",
        y="average_review_score",
        color="delivery_status",
        text="average_review_score",
        title="Average Review Score by Delivery Status"
    )

    fig.update_traces(
        texttemplate="%{text:.2f}"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# CUSTOMER EXPERIENCE
# ============================================================

st.header("⭐ 6. Customer Experience")


# ============================================================
# REVIEW SCORE DISTRIBUTION
# ============================================================

review_distribution_query = """

SELECT

    review_score,

    COUNT(*) AS review_count

FROM order_reviews

GROUP BY review_score

ORDER BY review_score;

"""


review_distribution_df = run_query(
    review_distribution_query
)


if not review_distribution_df.empty:

    st.subheader("⭐ Review Score Distribution")

    fig = px.bar(
        review_distribution_df,
        x="review_score",
        y="review_count",
        text="review_count",
        title="Distribution of Review Scores"
    )

    fig.update_xaxes(
        dtick=1
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# REVIEWS BY CATEGORY
# ============================================================

reviews_category_query = """

SELECT

    COALESCE(
        oi.product_category_name_english,
        'Unknown'
    ) AS category,

    ROUND(
        AVG(r.review_score)::numeric,
        2
    ) AS average_review_score,

    COUNT(*) AS reviews

FROM order_reviews r

JOIN order_items oi
    ON r.order_id = oi.order_id

GROUP BY category

HAVING COUNT(*) >= 10

ORDER BY average_review_score DESC

LIMIT 20;

"""


reviews_category_df = run_query(
    reviews_category_query
)


if not reviews_category_df.empty:

    st.subheader("🏷️ Reviews by Product Category")

    fig = px.bar(
        reviews_category_df,
        x="average_review_score",
        y="category",
        orientation="h",
        color="reviews",
        title="Average Review Score by Category"
    )

    fig.update_layout(
        yaxis=dict(
            categoryorder="total ascending"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# REVIEW SCORE VS DELIVERY DAYS
# ============================================================

review_delivery_scatter_query = """

SELECT

    EXTRACT(
        DAY FROM
        (
            o.order_delivered_customer_date
            -
            o.order_purchase_timestamp
        )
    ) AS delivery_days,

    r.review_score

FROM orders o

JOIN order_reviews r
    ON o.order_id = r.order_id

WHERE

    o.order_delivered_customer_date IS NOT NULL

    AND r.review_score IS NOT NULL;

"""


review_delivery_df = run_query(
    review_delivery_scatter_query
)


if not review_delivery_df.empty:

    st.subheader("📉 Delivery Time vs Customer Rating")

    fig = px.scatter(
        review_delivery_df,
        x="delivery_days",
        y="review_score",
        opacity=0.5,
        trendline="ols",
        title="Delivery Days vs Review Score"
    )

    fig.update_layout(
        xaxis_title="Delivery Days",
        yaxis_title="Review Score"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# PAYMENT ANALYSIS
# ============================================================

st.header("💳 7. Payment Analysis")


payment_query = """

SELECT

    payment_type,

    COUNT(DISTINCT order_id) AS orders,

    ROUND(
        SUM(payment_value)::numeric,
        2
    ) AS total_payment,

    ROUND(
        AVG(payment_value)::numeric,
        2
    ) AS average_payment

FROM order_payments

GROUP BY payment_type

ORDER BY total_payment DESC;

"""


payment_df = run_query(
    payment_query
)


if not payment_df.empty:

    col1, col2 = st.columns(2)

    with col1:

        fig = px.bar(
            payment_df,
            x="payment_type",
            y="total_payment",
            text_auto=".2s",
            title="Revenue by Payment Method"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        fig = px.pie(
            payment_df,
            names="payment_type",
            values="orders",
            hole=0.4,
            title="Orders by Payment Method"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# PAYMENT INSTALLMENTS
# ============================================================

installment_query = """

SELECT

    payment_installments,

    COUNT(*) AS transactions,

    ROUND(
        AVG(payment_value)::numeric,
        2
    ) AS average_payment

FROM order_payments

GROUP BY payment_installments

ORDER BY payment_installments;

"""


installment_df = run_query(
    installment_query
)


if not installment_df.empty:

    st.subheader("💰 Payment Installments Analysis")

    fig = px.bar(
        installment_df,
        x="payment_installments",
        y="transactions",
        title="Transactions by Number of Installments"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# SQL WINDOW FUNCTION ANALYSIS
# ============================================================

st.header("🏆 8. Advanced SQL Analysis")


window_query = """

WITH seller_revenue AS
(
    SELECT

        s.seller_id,

        s.seller_state,

        SUM(
            COALESCE(
                oi.item_total_value,
                oi.price + oi.freight_value
            )
        ) AS revenue

    FROM sellers s

    JOIN order_items oi
        ON s.seller_id = oi.seller_id

    GROUP BY
        s.seller_id,
        s.seller_state
),

ranked_sellers AS
(
    SELECT

        seller_id,

        seller_state,

        ROUND(
            revenue::numeric,
            2
        ) AS revenue,

        RANK() OVER(
            ORDER BY revenue DESC
        ) AS revenue_rank

    FROM seller_revenue
)

SELECT *

FROM ranked_sellers

WHERE revenue_rank <= 10

ORDER BY revenue_rank;

"""


window_df = run_query(
    window_query
)


if not window_df.empty:

    st.subheader("🥇 Top 10 Sellers Using SQL Window Function")

    st.dataframe(
        window_df,
        use_container_width=True
    )


# ============================================================
# ORDER STATUS ANALYSIS
# ============================================================

st.header("📦 9. Order Status Analysis")


order_status_query = """

SELECT

    order_status,

    COUNT(*) AS order_count

FROM orders

GROUP BY order_status

ORDER BY order_count DESC;

"""


order_status_df = run_query(
    order_status_query
)


if not order_status_df.empty:

    fig = px.pie(
        order_status_df,
        names="order_status",
        values="order_count",
        title="Order Status Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# FINAL DATA TABLE
# ============================================================

st.header("📋 10. Detailed Data")


tab1, tab2, tab3 = st.tabs(
    [
        "Monthly Sales",
        "Categories",
        "Top Customers"
    ]
)


with tab1:

    if not monthly_df.empty:

        st.dataframe(
            monthly_df,
            use_container_width=True
        )


with tab2:

    if not category_revenue_df.empty:

        st.dataframe(
            category_revenue_df,
            use_container_width=True
        )


with tab3:

    if not customer_spending_df.empty:

        st.dataframe(
            customer_spending_df,
            use_container_width=True
        )


# ============================================================
# PROJECT INSIGHTS
# ============================================================

st.header("📌 Business Insights")

st.markdown(
    """
    ### Key analysis areas

    **Sales**
    - Monthly revenue trend identifies growth and seasonal patterns.
    - Category revenue identifies major revenue-generating categories.
    - Product analysis identifies high-performing products.
    - State-level analysis shows geographic sales distribution.

    **Customers**
    - Customer distribution shows the concentration of customers by state.
    - Customer spending identifies high-value customers.
    - Repeat-customer analysis measures customer retention behavior.

    **Sellers**
    - Seller revenue identifies high-revenue sellers.
    - Seller order count measures seller activity.
    - Seller revenue vs orders helps identify sellers with high order volume
      and high monetary contribution.

    **Delivery**
    - Average delivery days measures operational performance.
    - On-time vs delayed orders shows delivery reliability.
    - State-level delivery analysis identifies geographic differences.
    - Delivery status can be compared with customer review scores.

    **Customer Experience**
    - Review-score distribution shows customer satisfaction patterns.
    - Category-level reviews identify categories with different rating patterns.
    - Delivery days vs review scores can reveal relationships between
      delivery experience and customer satisfaction.

    **Payments**
    - Payment-method analysis shows customer payment preferences.
    - Installment analysis shows how customers distribute payments.
    """
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "E-Commerce Analytics Dashboard | PostgreSQL + Pandas + Streamlit + Plotly"
)