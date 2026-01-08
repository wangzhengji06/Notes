from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterator, Optional, Tuple

import mlflow
import mlflow.pyfunc
import pandas as pd
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

MLFLOW_TRACKING_URI = ""


def configure_mlflow(tracking_uri: str = MLFLOW_TRACKING_URI) -> None:
    """
    Set the tracking uri to point to the current server
    """
    mlflow.set_tracking_uri(tracking_uri)


def set_experiment(experiment_name: str = "Default") -> None:
    """
    If not exists, create experiment with given name
    Else, set the experiment with that name
    """
    configure_mlflow()
    try:
        mlflow.create_experiment(experiment_name)
    except Exception:
        pass
    mlflow.set_experiment(experiment_name)


@contextmanager
def start_run(
    experiment_name: str = "Default", run_name: Optional[str] = None
) -> Iterator[mlflow.ActiveRun]:
    """
    Wrap the mlflow start run with set experiment_name
    """
    set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name) as run:
        yield run


@contextmanager
def start_child_run(
    run_name: Optional[str] = None,
) -> Iterator[mlflow.ActiveRun]:
    """
    Compared to start_run, it starts a child run
    """
    with mlflow.start_run(run_name=run_name, nested=True) as run:
        yield run


def log_params_flat(params: Dict[str, Any], prefix: str = "") -> None:
    """
    Log the training parameters with simple flattening
    """
    flat: Dict[str, Any] = {}

    def rec(obj: Any, path: str) -> None:
        if is_dataclass(obj):
            obj = asdict(obj)
        if isinstance(obj, dict):
            for k, v in obj.items():
                rec(v, f"{path}.{k}" if path else str(k))
        else:
            v = obj
            if not isinstance(v, (str, int, float, bool)) and v is not None:
                v = str(v)
            flat[f"{prefix}{path}" if prefix else path] = v

    rec(params, "")
    flat = {k: v for k, v in flat.items() if k}
    if flat:
        mlflow.log_params(flat)


def log_repro_artifacts(
    paths: Tuple[str, ...] = ("pyproject.toml", "poetry.lock", "docker"),
) -> None:
    """
    Log the repro artifacts.
    Please remember to add your source code here.
    """
    for p in paths:
        try:
            mlflow.log_artifact(p, artifact_path="repro")
        except Exception:
            pass


def get_client() -> MlflowClient:
    """
    You need to use the MlflowClient to set the alias
    """
    return MlflowClient()


def get_active_run_id() -> str:
    """
    Return the current run's run id
    """
    run = mlflow.active_run()
    if run is None:
        raise RuntimeError("No active MLflow run.")
    return run.info.run_id


## The following happens after the model is already fitted.


def log_sklearn_model(
    model,
    X_example: pd.DataFrame,
    y_example: Optional[pd.Series] = None,
    registered_model_name: Optional[str] = None,
) -> str:
    """
    Logs an sklearn model with signature + input_example.
    Returns the model_uri returned by MLflow.
    """
    signature = (
        infer_signature(X_example, y_example)
        if y_example is not None
        else infer_signature(X_example, model.predict(X_example))
    )

    model_info = mlflow.sklearn.log_model(
        sk_model=model,
        signature=signature,
        input_example=X_example.head(5),
        registered_model_name=registered_model_name,
    )
    return model_info.model_uri


def log_xgb_sklearn_model(
    model,
    X_example: pd.DataFrame,
    y_example: Optional[pd.Series] = None,
    registered_model_name: Optional[str] = None,
) -> str:
    """
    Logs an xgboost model with signature + input_example.
    Returns the model_uri returned by MLflow.
    """
    signature = (
        infer_signature(X_example, y_example)
        if y_example is not None
        else infer_signature(X_example, model.predict(X_example))
    )

    model_info = mlflow.xgboost.log_model(
        xgb_model=model,
        signature=signature,
        input_example=X_example.head(5),
        registered_model_name=registered_model_name,
    )
    return model_info.model_uri


def register_model_version(model_uri: str, registered_model_name: str) -> int:
    """
    Register the model_uri to the registered_model_name
    Return the version number
    """
    mv = mlflow.register_model(model_uri=model_uri, name=registered_model_name)
    return int(mv.version)


def set_alias(registered_model_name: str, alias: str, version: int) -> None:
    """
    set the alias for a regsitered model with specific version
    """
    client = get_client()
    client.set_registered_model_alias(
        name=registered_model_name, alias=alias, version=str(version)
    )


def get_alias_uri(registered_model_name: str, alias: str) -> str:
    """
    Will be used to retrieve the registered model for prediction
    """
    return f"models:/{registered_model_name}@{alias}"


def alias_exists(registered_model_name: str, alias: str) -> bool:
    """
    If not alias_exists, return False
    Used for situation of first run.
    """
    client = get_client()
    try:
        client.get_model_version_by_alias(name=registered_model_name, alias=alias)
        return True
    except Exception:
        return False


def get_alias_run_id(registered_model_name: str, alias: str) -> Optional[str]:
    """
    Returns the run_id associated with the model version pointed to by alias.
    """
    client = get_client()
    try:
        mv = client.get_model_version_by_alias(name=registered_model_name, alias=alias)
        return mv.run_id
    except Exception:
        return None


# Optional, You probably dont need it
# Mlflow only supports regressor/classfier
def evaluate_model(
    model_uri: str,
    test: pd.DataFrame,
    targets: str,
    model_type: str = "regressor",
    evaluators: list[str] | None = None,
) -> mlflow.models.EvaluationResult:
    """
    Evaluate the model.
    The evaluation result would be automatcially added to artifact
    The default here is shap.
    """
    if evaluators is None:
        evaluators = ["default"]
    return mlflow.models.evaluate(
        model=model_uri,
        data=test,
        targets=targets,
        model_type=model_type,
        evaluators=evaluators,
    )


# Only useful for hyperparameter tuning
def find_best_child_run(
    parent_run_id: str,
    metric_name: str,
    bigger_is_better: bool = True,
) -> Tuple[str, float]:
    """
    Get the best child run's id and the metric.
    """
    client = get_client()
    runs = client.search_runs(
        experiment_ids=[client.get_run(parent_run_id).info.experiment_id],
        filter_string=f"tags.mlflow.parentRunId = '{parent_run_id}'",
        max_results=10000,
        order_by=[f"metrics.{metric_name} {'DESC' if bigger_is_better else 'ASC'}"],
    )
    if not runs:
        raise RuntimeError("No child runs found under parent run.")
    best = runs[0]
    val = float(best.data.metrics.get(metric_name))
    return best.info.run_id, val


# Metric-Based Model Selector


class MetricComparer:
    """
    Used to compare run metrics vs baseline
    The comparison happens between the same metric
    """

    def __init__(
        self,
        bigger_is_better: bool,
        can_be_equal: bool,
        metric_name: str,
        threshold: float = 0.0,
    ) -> None:
        self.bigger_is_better = bigger_is_better
        self.can_be_equal = can_be_equal
        self.metric_name = metric_name
        self.threshold = threshold

    def _get_metric(self, run: mlflow.entities.Run, metric_name: str) -> float:
        """
        Get metric for a specific run
        """
        val = run.data.metrics.get(metric_name, None)
        if val is None:
            raise RuntimeError(
                f"Metric '{metric_name}' not found on run '{run.info.run_id}'. Was it logged?"
            )
        return float(val)

    def is_metric_better(
        self,
        candidate_run: mlflow.entities.Run,
        baseline_run: Optional[mlflow.entities.Run],
    ) -> bool:
        """
        Compare whether candidate_run is better than baseline_run for metric_name
        """
        if baseline_run is None:
            return True

        cand = self._get_metric(candidate_run, self.metric_name)
        base = self._get_metric(baseline_run, self.metric_name)

        if self.can_be_equal and cand == base:
            return True

        if self.bigger_is_better:
            return (cand - self.threshold) > base
        else:
            return (cand + self.threshold) < base


class ModelSelector:
    """
    Select wheter a candidate run can replace the champion model.
    """

    def __init__(
        self,
        candidate_run_id: str,
        registered_model_name: str,
        champion_alias: str = "champion",
        must_be_better_metric_comparers: Optional[Dict[str, MetricComparer]] = None,
        to_be_thresholded_metric_comparers: Optional[Dict[str, MetricComparer]] = None,
        min_hit_rate: float = 0.0,
    ) -> None:
        if (
            not must_be_better_metric_comparers
            and not to_be_thresholded_metric_comparers
        ):
            raise ValueError(
                "Both 'must_be_better_metric_comparers' and 'to_be_thresholded_metric_comparers' cannot be empty."
            )

        self.client = get_client()
        self.candidate_run = self.client.get_run(candidate_run_id)

        self.registered_model_name = registered_model_name
        self.champion_alias = champion_alias
        self.baseline_run = self._get_champion_run()

        self.must_be_better_metric_comparers = must_be_better_metric_comparers or {}
        self.to_be_thresholded_metric_comparers = (
            to_be_thresholded_metric_comparers or {}
        )
        self.min_hit_rate = float(min_hit_rate)

    def _get_champion_run(self) -> Optional[mlflow.entities.Run]:
        """
        Get the Run for that model's champion version
        """
        run_id = get_alias_run_id(self.registered_model_name, self.champion_alias)
        if run_id is None:
            return None
        return self.client.get_run(run_id)

    def is_selected(self) -> bool:
        """
        Hard gate: must_be_better_metric_comparers -> need to win
        Soft gate: hit rate -> can be 0
        """
        for metric_name, comparer in self.must_be_better_metric_comparers.items():
            if not comparer.is_metric_better(self.candidate_run, self.baseline_run):
                return False

        if not self.to_be_thresholded_metric_comparers:
            return True

        hits = []
        for comparer in self.to_be_thresholded_metric_comparers.values():
            hits.append(
                int(comparer.is_metric_better(self.candidate_run, self.baseline_run))
            )

        hit_rate = sum(hits) / len(hits)
        return hit_rate >= self.min_hit_rate


def promote_if_selected(
    candidate_version: int,
    candidate_run_id: str,
    registered_model_name: str,
    champion_alias: str,
    must_be_better: Dict[str, MetricComparer],
    soft_metrics: Optional[Dict[str, MetricComparer]] = None,
    min_hit_rate: float = 0.0,
) -> bool:
    """
    Convenience function:
    Compare candidate run vs current champion run via MetricComparers
    If selected, move alias to candidate version
    Returns True if promoted.
    """
    selector = ModelSelector(
        candidate_run_id=candidate_run_id,
        registered_model_name=registered_model_name,
        champion_alias=champion_alias,
        must_be_better_metric_comparers=must_be_better,
        to_be_thresholded_metric_comparers=soft_metrics or {},
        min_hit_rate=min_hit_rate,
    )

    if selector.is_selected():
        set_alias(registered_model_name, champion_alias, candidate_version)
        return True

    return False


def load_and_predict(model_uri: str, X: pd.DataFrame) -> pd.Series:
    """
    hmmmmm.... this should work for sklearn, xgboost and lightgbm etc
    it assumes the predict only take X
    """
    model = mlflow.pyfunc.load_model(model_uri)
    preds = model.predict(X)
    return pd.Series(preds, index=X.index, name="prediction")
