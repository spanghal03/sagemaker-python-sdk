# Copyright 2017-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

from mock import Mock, patch
from packaging import version
import pytest

from sagemaker.tensorflow import defaults, TensorFlow

REGION = "us-west-2"


@pytest.fixture()
def sagemaker_session():
    return Mock(name="sagemaker_session", boto_region_name=REGION)


def _build_tf(sagemaker_session, **kwargs):
    return TensorFlow(
        sagemaker_session=sagemaker_session,
        entry_point="dummy.py",
        role="dummy-role",
        train_instance_count=1,
        train_instance_type="ml.c4.xlarge",
        **kwargs
    )


@patch("sagemaker.fw_utils.empty_framework_version_warning")
def test_empty_framework_version(warning, sagemaker_session):
    estimator = _build_tf(sagemaker_session, framework_version=None)

    assert estimator.framework_version == defaults.TF_VERSION
    warning.assert_called_with(defaults.TF_VERSION, estimator.LATEST_VERSION)


@patch("sagemaker.fw_utils.python_deprecation_warning")
def test_estimator_py2_deprecation_warning(warning, sagemaker_session):
    estimator = _build_tf(sagemaker_session, py_version="py2")

    assert estimator.py_version == "py2"
    warning.assert_called_with("tensorflow", "2.1.0")


def test_py2_version_deprecated(sagemaker_session):
    with pytest.raises(AttributeError) as e:
        _build_tf(sagemaker_session, framework_version="2.1.1", py_version="py2")

    msg = (
        "Python 2 containers are only available with 2.1.0 and lower versions. "
        "Please use a Python 3 container."
    )
    assert msg in str(e.value)


def test_py2_version_is_not_deprecated(sagemaker_session):
    estimator = _build_tf(sagemaker_session, framework_version="1.15.0", py_version="py2")
    assert estimator.py_version == "py2"
    estimator = _build_tf(sagemaker_session, framework_version="2.0.0", py_version="py2")
    assert estimator.py_version == "py2"


def test_py2_is_default_version_before_tf1_14(sagemaker_session):
    estimator = _build_tf(sagemaker_session, framework_version="1.13")
    assert estimator.py_version == "py2"


def test_framework_name(sagemaker_session):
    tf = _build_tf(sagemaker_session, framework_version="1.15.2")
    assert tf.__framework_name__ == "tensorflow"


def test_enable_sm_metrics(sagemaker_session):
    tf = _build_tf(sagemaker_session, enable_sagemaker_metrics=True)
    assert tf.enable_sagemaker_metrics


def test_disable_sm_metrics(sagemaker_session):
    tf = _build_tf(sagemaker_session, enable_sagemaker_metrics=False)
    assert not tf.enable_sagemaker_metrics


def test_disable_sm_metrics_if_fw_ver_is_less_than_1_15(sagemaker_session, tf_version):
    if version.Version(tf_version) > version.Version("1.14"):
        pytest.skip("This test is for TF 1.14 and lower.")

    tf = _build_tf(sagemaker_session, framework_version=tf_version, image_name="old-image")
    assert tf.enable_sagemaker_metrics is None


def test_enable_sm_metrics_if_fw_ver_is_at_least_1_15(sagemaker_session, tf_version):
    if version.Version(tf_version) < version.Version("1.15"):
        pytest.skip("This test is for TF 1.15 and higher.")

    tf = _build_tf(sagemaker_session, framework_version=tf_version)
    assert tf.enable_sagemaker_metrics


def test_require_image_name_if_fw_ver_is_less_than_1_11(sagemaker_session, tf_version):
    if version.Version(tf_version) > version.Version("1.10"):
        pytest.skip("This test is for TF 1.10 and lower.")

    with pytest.raises(ValueError) as e:
        _build_tf(sagemaker_session, framework_version=tf_version)

    expected_msg = (
        "TF {version} supports only legacy mode. Please supply the image URI directly with "
        "'image_name=520713654638.dkr.ecr.{region}.amazonaws.com/"
        "sagemaker-tensorflow:{version}-cpu-py2' and set 'model_dir=False'. "
        "If you are using any legacy parameters (training_steps, evaluation_steps, "
        "checkpoint_path, requirements_file), make sure to pass them directly as hyperparameters instead."
    ).format(version=tf_version, region=REGION)

    assert expected_msg in str(e)