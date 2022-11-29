from pathlib import Path

import mlflow
import pytest
from mlflow_models import *
from mlflow_models import __all__ as MODELS
from pynavio._mlflow import _check_model_serving, _get_example_request_df, ModelValidator

from pynavio import infer_imported_code_path

# these require custom tests - see corresponding test_<model_name>.py
EXCLUDED_MODELS = [
    'car_price_model', 'timeseries', 'visual_inspection_model',
    'timeseries_trainer', 'pump_leakage_model', 'error_model'
]

MODELS = [*filter(lambda model: model not in EXCLUDED_MODELS, MODELS)]


@pytest.fixture(params=MODELS)
def model_name(request):
    return request.param


class Helper(ModelValidator):

    @staticmethod
    def setup_model(model_name, model_path, expect_error=False):
        assert model_name in [*MODELS, *EXCLUDED_MODELS]
        import mlflow_models

        setup_arguments = dict(with_data=False,
                               with_oodd=False,
                               explanations=None,
                               path=model_path,
                               code_path=[mlflow_models.__path__[0]])
        if expect_error:
            setup_arguments['expect_error_on_example_request'] = expect_error

        globals()[model_name].setup(**setup_arguments)


    @staticmethod
    def verify_model_output(model_output,
                            model_input=None,
                            expect_error=False,
                            **kwargs):
        if expect_error:
            expected_keys = {'error_code', 'message', 'stack_trace'}
            assert set(model_output.keys()) == expected_keys
            return

        key = 'prediction'
        assert key in model_output

        if model_input is not None:
            # this is not always the case, e.g. some timeseries models
            # will output only one prediction for a set of timeseries rows (frame)
            assert len(model_output[key]) == model_input.shape[0], \
                'The number of elements in the prediction array must match ' \
                'the number of input rows'

    @staticmethod
    def verify_model_serving(model_path, port=5001, request_bodies=None):
        try:
            _check_model_serving(model_path, port, request_bodies)
        except Exception:
            pytest.fail("Error in the model serving/prediction")

    def __call__(self, model_path, validate_model_serving=True, validation_port=5001,
                 expect_error: bool = False, **kwargs):
        self.setup_model(kwargs["model_name"], model_path, expect_error)
        super().__call__(model_path, validate_model_serving,
                         validation_port, expect_error, **kwargs)


@pytest.fixture
def helper():
    return Helper()
