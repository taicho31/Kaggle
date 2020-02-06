# https://xgboost.readthedocs.io/en/latest/parameter.html
import xgboost as xgb
def modelling_xgb(new_train, new_test):
    X_train = new_train.drop(['accuracy_group', 'game_session'],axis=1).copy()
    y_train = new_train.accuracy_group.copy()
    y_train.loc[y_train<=1]=0
    y_train.loc[y_train>=2]=1
    lbl = preprocessing.LabelEncoder()
    lbl.fit(list(X_train["installation_id"]))
    X_train["installation_id"] = lbl.transform(list(X_train["installation_id"]))
    remove_features = [i for i in X_train.columns if "_4235" in i or i == "world_"+str(activities_world["NONE"])] #or i in to_exclude]
    for i in X_train.columns:
        if X_train[i].std() == 0 and i not in remove_features:
            remove_features.append(i)
    X_train = X_train.drop(remove_features, axis=1)
    X_train = X_train[sorted(X_train.columns.tolist())]

    X_test = new_test.drop(["installation_id","accuracy_group", "game_session"], axis=1)
    X_test = X_test.drop(remove_features, axis=1)
    X_test = X_test[sorted(X_test.columns.tolist())]

    n_folds=5
    skf=GroupKFold(n_splits = n_folds)
    models = []
    xgb_params = {
    "objective" : "binary:logistic",
    "eval_metric" : "auc",
    "tree_learner": "serial",
    "metric": "auc",
    "max_depth" : 4,
    "boosting": 'gbdt',
    "num_leaves" : 13,
    "learning_rate" : 0.01,
    }

    valid = pd.DataFrame(np.zeros([X_train.shape[0]]))
    for i , (train_index, test_index) in enumerate(skf.split(X_train, y_train, X_train["installation_id"])):
        print("Fold "+str(i+1))
        X_train2 = X_train.iloc[train_index,:]
        y_train2 = y_train.iloc[train_index]
        X_train2 = X_train2.drop(['installation_id'],axis=1)

        X_test2 = X_train.iloc[test_index,:]
        y_test2 = y_train.iloc[test_index]
        X_test2 = X_test2.drop(['installation_id'],axis=1)
            
        xgb_train = xgb.DMatrix(X_train2, label = y_train2)
        xgb_eval = xgb.DMatrix(X_test2, label = y_test2)
        watchlist = [(xgb_train, "train"), (xgb_eval, "eval")]
        
        num_boost_round = 100000
        clf = xgb.train(
        xgb_params, xgb_train, num_boost_round, watchlist,
        early_stopping_rounds=100, verbose_eval = 500
        #evals_result=evals_result,
        #feval=crps_score,
    )

        models.append(clf)
        test_predict = clf.predict(xgb_eval, ntree_limit=clf.best_ntree_limit)            
        valid.iloc[test_index] = test_predict.reshape(X_test2.shape[0], 1)
        if i == 0:
            feature_importance_df = pd.DataFrame(list(clf.get_score(importance_type="total_gain").keys()), columns=["Features"])
        feature_importance_df["fold_"+str(i)] = pd.DataFrame.from_dict(clf.get_score(importance_type="total_gain").values())
    
    feature_importance_df["Average"] = np.mean(feature_importance_df.iloc[:,1:n_folds+1], axis=1)
    feature_importance_df["Std"] = np.std(feature_importance_df.iloc[:,1:n_folds+1], axis=1)
    feature_importance_df["Cv"] = feature_importance_df["Std"] / feature_importance_df["Average"]

    print("logloss = \t {}".format(log_loss(y_train, valid)))
    print("ROC = \t {}".format(roc_auc_score(y_train, valid)))
    print('Accuracy score = \t {}'.format(accuracy_score(y_train, np.round(valid))))
    print('Precision score = \t {}'.format(precision_score(y_train, np.round(valid))))
    print('Recall score =   \t {}'.format(recall_score(y_train, np.round(valid))))
    print('F1 score =      \t {}'.format(f1_score(y_train, np.round(valid))))
    print(confusion_matrix(y_train, np.round(valid)))
    pred_value = np.zeros([X_test.shape[0]])
    X_test = xgb.DMatrix(X_test)
    for model in models:
        pred_value += model.predict(X_test, ntree_limit=clf.best_ntree_limit) / len(models)
    return pred_value, valid, feature_importance_df
pred_value, valid, feature_importance_df = modelling_xgb(new_train, new_test)
