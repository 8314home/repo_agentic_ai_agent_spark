# System Architecture Documentation

## Executive Optimization Profile

This document outlines the optimization strategies implemented in the data processing pipeline, focusing on performance improvements and bottleneck resolutions. The primary goal is to enhance the efficiency of Spark operations while ensuring data integrity and accuracy.

### Initial Bottlenecks Identified
- **Level 1: Baseline Structural Issues**
  - The use of `inferSchema=True` can lead to performance overhead; explicitly defining the schema would optimize the read operation.
  - The filter condition for "Electronics" is applied after the tier calculation, which may lead to unnecessary processing of all records instead of filtering early.
  - There is no use of broadcast hints for potentially small DataFrames, which could optimize join operations if applicable.
  - The final write operation is coalesced into a single partition, which can lead to performance bottlenecks due to increased task execution time and potential memory issues.

- **Level 2: Advanced Processing & Session Issues**
  - The Spark session is initialized with `master("local[*]")`, which may not leverage distributed computing effectively for larger datasets.
  - There is no explicit configuration for shuffle partitions, which can lead to sub-optimal performance during operations that require shuffling data.
  - The use of a Python UDF for tier calculation introduces row-by-row processing, which is less efficient than using built-in Spark SQL functions that can leverage vectorized operations.
  - The counting operation for high-value transactions (`count()`) triggers a full DataFrame action, which can be costly in terms of performance, especially if the DataFrame is large.

## Experimental Benchmark Scorecard

| Optimization Strategy               | Execution Time (s) | Status      | Diagnostic Notes          |
|-------------------------------------|---------------------|-------------|---------------------------|
| Baseline Structural Optimization     | 2.3605s             | ✅ Success  | Executed smoothly.        |
| Advanced Engine Tuning              | 1.9073s             | ✅ Success  | Executed smoothly.        |

## Comprehensive Breakdown of Strategies and Errors/Plans

### Strategy 1: Baseline Structural Optimization
**Spark Catalyst Plan Details:**
```text
== Parsed Logical Plan ==
'Project [unresolvedstarwithcolumns(customer_tier, CASE WHEN '`>`('amount, 500) THEN High-Value WHEN '`>`('amount, 100) THEN Mid-Value ELSE Low-Value END, None)]
+- Filter (category#2982 = Electronics)
   +- Relation [transaction_id#2978,user_id#2979,amount#2980,country#2981,category#2982] csv

== Analyzed Logical Plan ==
transaction_id: string, user_id: string, amount: double, country: string, category: string, customer_tier: string
Project [transaction_id#2978, user_id#2979, amount#2980, country#2981, category#2982, CASE WHEN (amount#2980 > cast(500 as double)) THEN High-Value WHEN (amount#2980 > cast(100 as double)) THEN Mid-Value ELSE Low-Value END AS customer_tier#2984]
+- Filter (category#2982 = Electronics)
   +- Relation [transaction_id#2978,user_id#2979,amount#2980,country#2981,category#2982] csv

== Optimized Logical Plan ==
Project [transaction_id#2978, user_id#2979, amount#2980, country#2981, category#2982, CASE WHEN (amount#2980 > 500.0) THEN High-Value WHEN (amount#2980 > 100.0) THEN Mid-Value ELSE Low-Value END AS customer_tier#2984]
+- Filter (isnotnull(category#2982) AND (category#2982 = Electronics))
   +- Relation [transaction_id#2978,user_id#2979,amount#2980,country#2981,category#2982] csv

== Physical Plan ==
*(1) Project [transaction_id#2978, user_id#2979, amount#2980, country#2981, category#2982, CASE WHEN (amount#2980 > 500.0) THEN High-Value WHEN (amount#2980 > 100.0) THEN Mid-Value ELSE Low-Value END AS customer_tier#2984]
+
```

### Strategy 2: Advanced Engine Tuning
**Spark Catalyst Plan Details:**
```text
== Parsed Logical Plan ==
'Project [unresolvedstarwithcolumns(customer_tier, CASE WHEN 'isNull('amount) THEN Unknown WHEN '`>`('amount, 500) THEN High-Value WHEN '`>`('amount, 100) THEN Mid-Value ELSE Low-Value END, None)]
+- Filter (category#3017 = Electronics)
   +- Relation [transaction_id#3013,user_id#3014,amount#3015,country#3016,category#3017] csv

== Analyzed Logical Plan ==
transaction_id: string, user_id: string, amount: double, country: string, category: string, customer_tier: string
Project [transaction_id#3013, user_id#3014, amount#3015, country#3016, category#3017, CASE WHEN isnull(amount#3015) THEN Unknown WHEN (amount#3015 > cast(500 as double)) THEN High-Value WHEN (amount#3015 > cast(100 as double)) THEN Mid-Value ELSE Low-Value END AS customer_tier#3019]
+- Filter (category#3017 = Electronics)
   +- Relation [transaction_id#3013,user_id#3014,amount#3015,country#3016,category#3017] csv

== Optimized Logical Plan ==
Project [transaction_id#3013, user_id#3014, amount#3015, country#3016, category#3017, CASE WHEN isnull(amount#3015) THEN Unknown WHEN (amount#3015 > 500.0) THEN High-Value WHEN (amount#3015 > 100.0) THEN Mid-Value ELSE Low-Value END AS customer_tier#3019]
+- Filter (isnotnull(category#3017) AND (category#3017 = Electronics))
   +- Relation [transaction_id#3013,user_id#3014,amount#3015,country#3016,category#3017] csv

== Physical Plan ==
*(1) Project [transaction_id#3013, user_id#3014, amount#3015, country#3016, category#3017, CASE WHEN isnull(amoun
```

## Technical Rationale Supporting the Selected High-Performance Choice

The optimizations implemented focus on reducing unnecessary computations and leveraging Spark's distributed processing capabilities. By explicitly defining schemas, filtering data early, and avoiding row-by-row processing with UDFs, we can significantly enhance performance. The successful execution of both optimization strategies demonstrates the effectiveness of these approaches in addressing the identified bottlenecks and improving overall processing time. 

In conclusion, the strategies outlined in this document provide a robust framework for optimizing Spark applications, ensuring efficient data processing and resource utilization.