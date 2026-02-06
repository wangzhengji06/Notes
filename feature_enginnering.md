## 1. Variable Types

Mainly 4 types of datas.

1. Numerical Variables
2. Categorical Variables
3. Date and time Variables
4. Mixed Variables

## 2. Variable Characteristics

Missing Data -> Interfere with sklearn training
Cardinality -> When a categorical features have too many values, could cause overfitting
Rare Lables -> Exist in train set but not in test set, easily overfitting the model
Variable Distribution -> Determines latter feature engineering strategy, like median -> skewed, mean -> normal in missing data imputation
Outliers -> Checked using boxplots, again you need to see the distribution to determine what method to use to detect outliers
Linear Model Distribution -> Checks to perform before using Linear model

## 3. Missing Data Imputation

### Missing Reason

1. MCAR
   Missing completely at random, has nothing to do with the feature and other features.

2. MAR
   Missing at random, has nothing to do with feature itself but impacted by other features.

3. MNAR
   Missing not at random, has something to do with the value of the feature itself.

### Basic Method

Categorical -> Mode(Data Missing at Random) / "Missing"(Data Not Missing at Random)
Numerical -> Median / Mean(Data Missing at Random), 99999, -1, 0 etc,(Data Not Missing at Random)

Marker -> This is a missing data

A rule of thumb is, if it is tree-based model, you can use "Missing" and 999999
if it is linear-based model, you should use mode, median and mean.
But a missing data marker can always be good if you do not mind increasing dimension.

### Alternative Method

1. Complete Case Analysis (MCAR)
   only remain the row with data in all of the variables, the underlying assumption is the data is missing at random
   In practice, this usually done to column with less than 5% na.
   To check whetehr this is safe, check the variable distribution after getting rid of NA to show that the distribution is still the same

2. End of tail imputation (MNAR)
   Actually the same as arbitrary value imputation, but the value is automatically selected.
   The underlying assumption is that data not missing at Random.
   The value is calculated using the outlier interval, but this time we want to pick outlier value

3. Random sample imputation (MCAR, MAR)
   Randomly impute the missing data from a pool of choices
   Still data missing ar Random assumption.
   Better than mean/mean/medai -> preserve variance and outlier
   Set the seed using other important variables so that it will create simliar feature for missing values! Unexpected imputation might be risky
   It will preservce the variance but not covariance

4. Mean / median per group (MAR)
   Yes the idea is exactly what you inferred from the method
   Mean/median imputation + missing indicator + group number(if you are using mean grouped by gender, then you can assign group key)

### Rule of Thumb

1. Can variable be NA? -> No, then CCA.
2. Yes, Is the model linear? -> Yes, mean/median & missing indicators for numerical, arbitrary for categorical.
3. Not linear model, then end tail for numerical, arbitrary for categorical.

### Multivariate Method

Use other features to impute one feature. Usually three main methods. KNN, MICE, and MissForest.

1. KNN -> train a KNN using other variables, find the k closest neighbors, determine the weighted average of the K neighbors.
   How to find k? Well, you can view it as a parameter in the training pipeline and use grid search and cross validation for it.
   KNN assumes MAR.

2. MICE -> We impute the NA using mean imputation, and values in 1 variable are reverted to NA, then the variable is modeled upon other varaibles. NAs are replaced by model predictions.
   This procedure continues for more than one rounds, usually 10 imputation cycles are needed.
   MICE assumes MAR. It is not psossible to automate with current tools.

3. missForest -> It is an extension of MICE using random forest. The author claims that this is the best method of imputing missing values.

## 4. Categorical Encoding

### Basic Method (Unsupervised ones)

Basically there are three basic ways of encoding: one hot encoding, oridinal encoding and count or frequency encoding.
One-hot-encoding is suitable for Linear model, ordinal/label encoding is suitable for tree based model, and count of frequency encoding is widely used in Kaggle.

1. One-hot-encoding
   If you have k categories, you use k-1 to prepresent dummy variables. However, if you - 1, are buidling a tree algorithm 2, are doing feature selection using recursive algorithm 3,interested in determining importance of each single cateogry - , then you can choose k dummy variables.
   One-hot-encoding might be good for lienar model and also assumes no distribution for categorical model, but when the feature is of high cardnality, the one-hot-encoding will expand the feature space largely.

2. Ordinal encoding
   Replace the categories by digits from 1 to n (or 0 to n-1), this is usually for quick benchmarking. Could be good for tree model.

3. Count or Frequency encoding
   Categories are replaced by the count or percentage of observation that show that category in the dataset. The limitation is, if two categories have exactly the same frequency / counts, it would appear that they are the same. May work well with tree model.

Unseen category might happen for all three methods. Unseen categories might be caused by rare labels and high cardinality.
If one-hot-encoding -> The unseen category will have 0 for all entries. In feature engine, if all 0, it basically blends in with the dropped category
If ordinal or count -> The unseen category will cuase a crash.... In feature engine, you can replace with -1 / 0.

In general: sometimes maybe an error is thrown is better, because at least you understand more about your data.

### Monotonic

Three ways. Ordered label encoding, Mean encoding, and weight of evidence.

1. Ordered label encoding: like ordinal encoding, but the value is assgined by the mean of the target in each categories. The higher the value of the mean, the lower the rank is.
   It is good that it does not expand the feature space, and creates monotonic relationship between categories and target. Might be good for both linear and nonlinear.

2. Mean encoding: replace the category by the average target value for that category. This has the same advantage of ordered label encoding, but if two categories has the same mean, they will be represented by the same value.
   A poteintail problem here is, if there are rare labels, the mean cannot actually represent the population for that rare category. So, we need to smooth the mean. How? When a category has too few rows, we use the target mean for the WHOLE DATASET instead of mean of that group. Then, $Value=\lambda * posterior + (1-\lambda) * prior$. Here the featire engine has a fixed value which might be better. The intuition here is, the higher the variance of that group, the more likely you should trust the population mean over group mean.
   Good for tree and bad for linear.

3. Weight of evidence: $WOR = ln{frac{positive per category / total positive observations}{negative per category / total negative observations}}$. The weakness is that when the denominator and numerator are 0, this value is basically undefined. In feature engine, if you meet this, you need to group them into a big rare label group. Only for binary classification.
   Good for tree.

Unseen cateogry handling: for mean encoding, you can get the overall target mean back. For weight of evidence, Feature-engine would just return error.

### Rare Labels

High cardinality and rare lables are like two sides of a coin. The problem is some is shown in train set but not shown in test set. Also, it might cause overfitting.
There are two ways to deal with this: 1. One hot encoding the frequent categories 2. Grouping rare labels

1. One hot encoding the frequent categories: maybe good for linear models. It does not keep the ignored information.

2. Rare Label encoding: Nothing much to say, you set a threshold and you group the rare labels.

## 5. Variable Transformation

We always want the skewed varaibles to be transformed so that they look more guassian like. For example, when using linear regression, we always assume that 1. Linearlity, 2. Residuals are randomly distributed, 3.Homoscedasticity, at each level the residual terms should be constant.
BTW, if you are not using linear model, there is no point in transforming the data.

Logarithm transformation: Positive data with righ-skewed distribution

Reciporal transformation: Population density

Square root transformation: Variables with a Poisson Distribution

Arcsin transformation: Dealing with probability, percentages and proportions

Power transformation: X^lambda. if right-skewed, then < 1. If left-skewed, then > 1.

Box-cox transformation: includes actually all the transformation we talked above.... It is only suitable for positive values, if it is not, add a constant, or use Yeo-Johnson

Yeo-Josn transformation: can deal with the negative value pretty easily

### Wrap up

The two mostly used transformations are Log transformation and Box-Cox. It is not necessary when we are training non-linear model.
The most important thing is, when you make the transformation, you should look at the before vs after distribution!
For example, it might not be wise to transfrom unifrom and Bimodel distribution.

## 6. Discretization

Discretization is the process of transforming continuous variables into discrete variables by creating a set of contiguous intervals that span the range of the variable's values.
Why do we do that?

1. Improve performance.
2. Reduce training time.
3. Mitigate the effect of outliers.
4. Create simpler features.

Especially with tree models! Discretization reduce the training time for the model.

There are mainly two questions when implementing: 1. How do we determine the interval limits? 2. How do we determine the number of intervals?
Unsupervised: Equal-Width, Equal-Frequency, Arbitrary, Binarization, K means
Supervised: Decision Trees, Chi-Merge, CAIM

Unsupervised models would need to be given the number of intervals while supervised models find the optimal number of bins.

### Basic Methods

1. Equal Width: width = (max_value - min_value) / N N is chosen by us.
   It does not improve value spread, but handles the outliers, and is good to combine with categorical encodings.

2. Equal Frequency: Divide by quantile instead of width.
   It will make the value spread more homogeneous, handles the outlier, and is good to combine with categorical encodings.

3. Arbitrary Discretization: We rule the interval. For example, 0-18 belongs to one group etc...
   It may or may not change the shapes of the original varaible depending on how we create the intervals.

### Adding categorical encoding strategy

Sometimes adding discretization with categorical encoding can be very useful. Especially for linear model, sometimes using a simple frequency discretization + ordered label encoding can do magic.
Why? for example for the bins we get, we use ordered label encoding, thus creating a monotonic relationship for the linear model, which can of course be benificial.

### Advanced Methods (Sklearn implementation)

1. K-means discretisation: Applying k-means clustering to the continuous variables
   Does not improve value spread, does handle outliers, good to combine with categorical encodings. This is only available in scikit-learn!

2. Using Classification Tree: It uses the prediction target to train a classfication tree to seperate the varaibles into different groups.
   Does not improve value spread, does handle outliers, and creates monotonic relationship with target value.
   The tricky part here is, you should find the target_prob calculated by decision tree being monotonic at least... if on test it is not, then we are overfitting.
   Also, we need to do parameter tuning. So this requires some experience.
   Here the feture_engine is a better framework to use for sure. But the important thing here is, if on test set it is not monotonic(not that strict), maybe you should consider doing something to save.

3. Binarization
   Binarization consists in transforming numerical features into a binary variable. Values above a certian threshold are mapped to 1, and others are mapped to 0
   This is common for sparse data.

## 7. Outliers

An outlier is a data point that is significantly different from remaining data. It can effect linear model and adaboost.

Here are the following ways.

1. Trimming -> Remove outliers from dataset.
2. Missing Data -> Treat the outliers as missing values and perform missing data imputation.
3. Discretization -> Put outliers into upper/lower bins
4. Censoring -> Cap the maximum and minimum value that you can take. Any values that are larger or smaller would be replaced with the allowed values.

How do we detect outliers btw? This is actually covered in section 3, by using Gaussian distribution and Inter-quantile range proximity rule. They are very important for methods like trimming and censoring.
Also you can use qunantile if you wish to.

For Censoring I strongly suggest adopting feature engine as it allows for arbitrary capping.

## 8. Datetime variables

Datetime variables are the variables that contain either date or time or both. (Date ot birth, date of application etc)

1. Of course, we can extract day, month and year.Also quarter of the year, week of the year etc.
2. Cyclical feature. Those that repeat their values at regular intervals. hours, days of week, week of the year, months, quarters, seasons etc.. We can use sin and cos to let ML model knows.

## 9. Engineering Mixed Variables

There are two types of mixed vairables.

1. Numbers or strings (1-100, U, T, M) / (1-3, D, A)
2. Numbers and strings (A15, B18, Postcode...)

The strategy is basically the same: extract the numerical AND the categorical part.

## 10. Feature Creation

Several ways:

1. Combine many variables with Math Function -> Sklearn, Feature Engine
2. Combine two variables with Math Function -> Sklearn, Feature Engine
3. Combine features with decision tree -> Sklearn
4. Polynomial Expansion -> Sklearn
5. Spline Feature

Math Funcion: Sum, Average, Max / Ratio, Substraction

Polynomial Features: Linear Model assumes a linear relationship, while sometimes a power of a variable might be linear to target.
It is also very common to use interaction of two variables. The important thing here is usually the power should not exceed 3 or 4.

Features from Decision Tree: The main idea is, some feature is not monotonic with target, so this relationship cannot be used by linear model.
However, using decision tree can replace the outputs of decision tree trained on the individual features, or combinations of 2 or 3 variables.
It introduces non-linearity, but it might make the transformed features look complex and hard to interept.

## 11. Feature Scaling

Feature magnitude matters: 1. Coefficient is influenced. 2. Bigger Coefficient dominates. 3. Gradient Descent converges faster. 4. Decreases the time for SVM. 5. Euclidean distance senstive to feature magnitude.

Only tree models dont care about feature scaling.

Different from variable transformation, Feature scaling (Except normalisation) does not change the shape of the distribution.

There are several methods:

1. Standardisation: X - mean / std, Presevces the shape, preserves outlier.

2. Mean normalisation: X - mean / (Max - Min), makes the values in between -1 and 1.

3. Scaling to maximum and minimum: X - Min / (Max - Min), preserves outlier. The value is not normalized, so the use of variable transformation is needed.

4. Scaling to absolte maximum: X / |Max|, all values betwee -1 and 1. Good for data that is centered and sparse matrix.

5. Scaling to median and quantile: X - median / (75th - 25th), very robust against outliers

6. Scaling to unit norm: Divide each feature vector by either Manhattan distance or Euclidean distance. This is not used for regression / classification, but you should use it for clustering....

Tricky Question: Should you apply feature scaling on categorical variables?
Because some machine learning models use numerical inputs only, it is necessary to transform on categorical variables. However, should we apply variable transformations?

1. One-hot encoding: If that is the case, and you use min-max, then we get the same result. So no need to to transform.
2. Mean encoding: Already return value in between 0 and 1, so do not need to scale those variables.
3. Weight of Evidence: Return values in a logit scale, so no need to scale.
4. Ordinal Encoding/Mean ENcoding when it is not binary: The value returned is not in between [0, 1] or [-1, 1], so we should scale the variables.

Which scaling method to use? Just choose the one with the best performance overall. Because categorical variables do not have statistical parameter interpretation value.

## 12. Putting it all together

Data Analaysis -> Feature Engineering

1. Check numerical, categorical, date/time, mixed ....
2. Missing data -> Categorical encoding -> Linear model assumptions -> Distribution -> Outliers -> Feature Magnitue

It seems that feature engine's pipeline covers more techniques...
