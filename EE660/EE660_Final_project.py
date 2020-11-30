import pandas
import missingno as mno
import matplotlib.pyplot as plt
from sklearn import linear_model
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.mixture import BayesianGaussianMixture

f_handle = pandas.read_csv('credit_train.csv')
N = f_handle.shape[0]
D = f_handle.shape[1]



                                        ### Split the data
# split the data into train and test first  ---> 10% test and 90% training
f_handle.drop(f_handle.tail(514).index, inplace=True)
X_test = f_handle.iloc[:N//10, :]
X_train = f_handle.iloc[N//10:, :]





                                         ### PREPROCESSING
# inspect the training data
#print(X_train.head())
# get the feature names
name_lst = f_handle.columns
#print(name_lst)
# get rid of irrelevant information such as Loan ID and Customer ID
X_train = X_train.iloc[:, 2:]
# Construct y_train
y_train = X_train.iloc[:, 0]
X_train = X_train.iloc[:, 1:]
#print(X_train.dtypes)


# check for missing data number
#print(X_train.isnull().sum())
#print(y_train.isnull().sum()) # there is no missing data in y label
mno.matrix(X_train, figsize=(20, 20))
#plt.show()


# ways to deal with missing data
# convert categorical data to numeric
# count each category
# categorical column = ['Term', 'Years in current job?', 'Home Ownership', 'Purpose']
#print(X_train['Term'].value_counts(), X_train['Years in current job'].value_counts(),
      #X_train['Home Ownership'].value_counts(), X_train['Purpose'].value_counts())
cleanup_data = {'Term': {'Short Term': -1, 'Long Term': 1},
                'Years in current job': {'< 1 year': 0, '1 year': 1, '2 years': 2, '3 years': 3, '4 years': 4,
                                         '5 years': 5, '6 years': 6, '7 years': 7, '8 years': 8, '9 years': 9, '10+ years': 10},
                'Home Ownership': {'Rent': 0, 'Own Home': 1, 'HaveMortgage': 3, 'Home Mortgage': 4}}
X_train.replace(cleanup_data, inplace=True)
#print(X_train.dtypes)

# drop purpose columns, two many categories, hard to convert
#X_train['Months since last delinquent'] = X_train['Months since last delinquent'].replace('np.nan', 0)
X_train = X_train.drop(['Purpose', 'Months since last delinquent'], axis=1)
#X_train['Years in current job'] = X_train['Years in current job'].astype(float)
#print(X_train.dtypes)
# NA in months since last delinquent means not late for every payment
missing_columns = ['Credit Score', 'Annual Income', 'Years in current job', 'Bankruptcies', 'Maximum Open Credit',
                   'Tax Liens']
# deterministic regression imputation


def random_imputation(df, feature):
    number_missing = df[feature].isnull().sum()
    observed_values = df.loc[df[feature].notnull(), feature]
    df.loc[df[feature].isnull(), feature + '_imp'] = np.random.choice(observed_values, number_missing, replace=True)
    return df


for feature in missing_columns:
    X_train[feature + '_imp'] = X_train[feature]
    X_train = random_imputation(X_train, feature)


deter_data = pandas.DataFrame(columns=['Det' + name for name in missing_columns])
for feature in missing_columns:
    deter_data['Det'+feature] = X_train[feature+'_imp']
    parameters = list(set(X_train.columns) - set(missing_columns) - {feature+'_imp'})

    model = linear_model.LinearRegression()
    model.fit(X=X_train[parameters], y=X_train[feature+'_imp'])

    deter_data.loc[X_train[feature].isnull(), 'Det' + feature] = \
        model.predict(X_train[parameters])[X_train[feature].isnull()]

# finish filling missing data put predict values back to X_train
for feature in missing_columns:
    X_train[feature] = deter_data['Det' + feature]
#mno.matrix(X_train, figsize = (20,16))
#plt.show()

# assign Charged Off as 0, Fully Paid as 1
'''y_label = []
for label in y_train:
    if label == 'Paid Off':
        y_label.append(1)
    else:
        y_label.append(0)'''
label_cleanup = {'Fully Paid': 1, 'Charged Off': 0}
y_train.replace(label_cleanup, inplace=True)

# normalization
# normalize all numeric data
cols_to_norm = ['Current Loan Amount', 'Credit Score', 'Annual Income', 'Monthly Debt', 'Current Credit Balance',
                'Maximum Open Credit']
X_train[cols_to_norm] = X_train[cols_to_norm].apply(lambda x: (x - x.min())/(x.max()-x.min()))



                    ### Now we are ready to test out different machine learning algorithms

# in mind: logistic regression, random forest, SVM
# cross validation
kf = StratifiedKFold(n_splits=5)
error = 0
lr_error = 0
rf_error = 0
iteration = 1
for train_index, test_index in kf.split(X_train, y_train):
    X_cv_train, X_cv_test = X_train.iloc[train_index], X_train.iloc[test_index]
    y_cv_train, y_cv_test = y_train.iloc[train_index], y_train.iloc[test_index]

    # logistic regression
    lr_clf = LogisticRegression()
    lr_clf.fit(X_cv_train, y_cv_train)
    y_pred = lr_clf.predict(X_cv_test)
    y_cv_test_lst = y_cv_test.values.tolist()

    error = 0
    for i in range(len(y_pred)):
        if y_pred[i] != y_cv_test_lst[i]:
            error += 1
    print('interation{} \nlogistic regression accuracy {}%'.format(iteration, (1-error/len(y_pred))*100))
    lr_error += error

    ''''# SVM
    clf = SVC(kernel='poly')
    clf.fit(X_cv_train, y_cv_train)
    y_pred = clf.predict(X_cv_test)
    y_cv_test_lst = y_cv_test.values.tolist()

    error_svm = 0
    sum_error_svm = 0
    for i in range(len(y_pred)):
        if y_pred[i] != y_cv_test_lst[i]:
            error_svm += 1
    sum_error_svm += error_svm
    print(error_svm/len(y_pred))'''


    # random forest
    error = 0
    clf = RandomForestClassifier()
    clf.fit(X_cv_train, y_cv_train)
    y_pred = clf.predict(X_cv_test)
    y_cv_test_lst = y_cv_test.values.tolist()
    for i in range(len(y_pred)):
        if y_pred[i] != y_cv_test_lst[i]:
            error += 1
    print('ramdom forest accuracy {}%'.format((1-error/len(y_pred))*100))

    ''''# k nearest neighbor
    error_knn = 0
    neigh = KNeighborsClassifier(n_neighbors=5)
    neigh.fit(X_cv_train, y_cv_train)
    y_pred = neigh.predict(X_cv_test)
    y_cv_test_lst = y_cv_test.values.tolist()
    for i in range(len(y_pred)):
        if y_pred[i] != y_cv_test_lst[i]:
            error_knn += 1
    print(error_knn / len(y_pred))'''

    # Gaussian Mixture Model
    '''error_GM = 0
    g = BayesianGaussianMixture(n_components=2)
    g.fit(X_cv_train, y_cv_train)
    y_pred = g.predict(X_cv_test)
    y_cv_test_lst = y_cv_test.values.tolist()
    for i in range(len(y_pred)):
        if y_pred[i] != y_cv_test_lst[i]:
            error_GM += 1
    print(error_GM / len(y_pred))'''
    iteration += 1
    
print('\n\nlogisitc regression average error {}%, accuracy is {}%'.format(lr_error/5/len(y_pred)*100, (1-(lr_error/5/len(y_pred)))*100 ))
print('random forest average error {}%, accuracy is {}')

