import pytest

import pynavio

import jsonschema


@pytest.mark.parametrize(
    "args",
    [
        # both arguments not set
        (dict()),
        # artifacts is set, but does not contain example_request
        ({
            pynavio.mlflow.ARTIFACTS: {
                'model_path': "a_path"
            }
        }),
        # artifacts is set, example_request file path does not exist
        ({
            pynavio.mlflow.ARTIFACTS: {
                'example_request': "non_existent_path"
            }
        })
    ])
def test_register_example_request_negative(args, tmpdir):
    with pytest.raises(AssertionError):
        pynavio.mlflow.register_example_request(tmpdir, **args)


PREDICTION_KEY = 'prediction'


@pytest.mark.parametrize(
    "model_output",
    [
        ({PREDICTION_KEY: 5}),
        ({PREDICTION_KEY: 5.0}),
        ({PREDICTION_KEY: "test"}),
        ({PREDICTION_KEY: "bool"}),
        ({PREDICTION_KEY: []}),
        ({PREDICTION_KEY: {}}),
        ({PREDICTION_KEY: [{}]}),
        ({PREDICTION_KEY: [[1], [2]]}),
        ({PREDICTION_KEY: [8.5, {}]}),
        ({PREDICTION_KEY: [8.5, "f"]}),
        ({PREDICTION_KEY: [8.5, True]}),
        ({PREDICTION_KEY: ["True", True]})

    ])
def test_prediction_schema_check_negative(model_output):
    with pytest.raises(jsonschema.exceptions.ValidationError):
        pynavio.mlflow.ModelValidator.verify_model_output(model_output)


@pytest.mark.parametrize(
    "model_output",
    [
        ({PREDICTION_KEY: [5]}),
        ({PREDICTION_KEY: [5],
          "extra key": 7,
          "other extra": {"more info": []}}),
        ({PREDICTION_KEY: [5.1, 5.0]}),
        ({PREDICTION_KEY: ["a", "b"]}),
        ({PREDICTION_KEY: [True, False, True]}),
    ])
def test_prediction_schema_check_positive(model_output):
    try:
        pynavio.mlflow.ModelValidator.verify_model_output(model_output)
    except(jsonschema.exceptions.ValidationError, AssertionError):
        pytest.fail("Unexpected Exception")


call_kwargs = {'append_to_failed_msg': ' Failed !!!',
               'append_to_succeeded_msg': ' Succeeded !!!'
               }


@pytest.mark.parametrize(
    "call_kwargs, msg",
    [
        ({}, ''),
        (call_kwargs, call_kwargs['append_to_succeeded_msg']),
    ])
def test_ModelValidator_call_positive(monkeypatch, capfd, call_kwargs, msg):
    def mock_run(self, path, **kwargs):
        pass

    monkeypatch.setattr('pynavio.mlflow.ModelValidator._run', mock_run)
    pynavio.mlflow.ModelValidator()('path/to/model', **call_kwargs)
    out, err = capfd.readouterr()
    expected_msg = f"{pynavio.mlflow.pynavio_model_validation}:" \
                   f" Validation succeeded.{msg}\n"
    assert out == expected_msg


@pytest.mark.parametrize(
    "call_kwargs, msg",
    [
        ({}, ''),
        (call_kwargs, call_kwargs['append_to_failed_msg']),
    ])
def test_ModelValidator_call_negative(monkeypatch, capfd, call_kwargs, msg):
    def mock_run(self, path, **kwargs):
        assert False

    monkeypatch.setattr('pynavio.mlflow.ModelValidator._run', mock_run)
    with pytest.raises(AssertionError):
        pynavio.mlflow.ModelValidator()('path/to/model', **call_kwargs)
    out, err = capfd.readouterr()
    expected_msg = f'{pynavio.mlflow.pynavio_model_validation}: ' \
                   f'Validation failed. Please fix' \
                   f' the identified issues before' \
                   f' uploading the model.{msg}\n'

    assert out == expected_msg
