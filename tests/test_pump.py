from glc_sensor_measurements.pump import ImatecPump
import pytest


def test_volume_type1_format_parsing():
    # given the volume in terms of milliliter
    volume_format = '1234E-4'

    # when
    float_value = ImatecPump.parse_volume_type_one_two_to_float(volume_format)

    # then
    assert float_value == pytest.approx(1.234e-7)


def test_volume_type2_format_parsing():
    # given
    volume_format = '1234-4'

    # when
    float_value = ImatecPump.parse_volume_type_one_two_to_float(
        volume_format
    )

    # then
    assert float_value == pytest.approx(1.234e-7)


def test_float_to_volume_type2_format_parsing():
    # given
    volume = 1.234e-7

    # when
    encoding = ImatecPump.float_to_volume_type_two(volume)

    # then
    assert encoding == '1234-4'
