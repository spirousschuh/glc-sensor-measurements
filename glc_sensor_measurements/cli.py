import click
from concurrent.futures import ThreadPoolExecutor
import datetime
import grpc
import logging
from threading import Thread


from glc_sensor_measurements.gRPC_command_center.sensor_pb2_grpc import \
    add_GlucoseSensorServicer_to_server
from glc_sensor_measurements.server import GlucoseSensorServicer
from glc_sensor_measurements.gRPC_command_center import GlucoseSensorStub
from glc_sensor_measurements.gRPC_command_center.sensor_pb2 import \
    MonitoringRequest, RecordingRequest, VolumeRequest


@click.group('Driver for the glucose / lactate sensor')
def measure():
    pass


@measure.group(name='server', help='host sensor and pump')
def server():
    pass


@server.command(help='Start Sensor Server')
@click.option(
    '--pump-port',
    help='port for reaching the pump '
         '(more info: python -m serial.tools.list_ports)',
    type=str,
    required=True,
)
@click.option(
    '--sensor-port',
    help='port for reaching the sensor spot '
         '(more info: python -m serial.tools.list_ports)',
    type=str,
    required=True,
)
@click.option(
    '--storage-directory',
    help='directory whre to store all the files',
    type=str,
    required=True,
)
def start(pump_port, sensor_port, storage_directory):
    sensor_and_pump_servicer = GlucoseSensorServicer()
    sensor_and_pump_servicer.establish_pump_connection(pump_port)
    logging.info('Established connection to pump on port %s' % pump_port)

    sensor_and_pump_servicer.establish_sensor_connection(sensor_port)
    logging.info('Established connection to sensor on port %s' % sensor_port)

    sensor_and_pump_servicer.set_storage_location(storage_directory)
    logging.info(
        'Files will be stored in the directory: %s' % storage_directory
    )

    get_sensor_values = Thread(
        target=sensor_and_pump_servicer.record_measurements_forever
    )
    get_sensor_values.start()

    sensor_server = grpc.server(ThreadPoolExecutor(max_workers=5))
    add_GlucoseSensorServicer_to_server(
        sensor_and_pump_servicer,
        sensor_server,
    )
    sensor_server.add_insecure_port('[::]:50051')
    sensor_server.start()

    click.echo('started the server for pump and sensor')
    sensor_server.wait_for_termination()


@measure.group(name='client', help='Remote control')
def client():
    pass


@client.command(
    help='Record the values from the sensor and write them to a csv file'
)
@click.option(
    '--name',
    help='the name of the measurement that is used for storing the csv file',
    type=str
)
@click.option(
    '--real-glucose',
    help='the concentration [g / L] of glucose if known (default: NaN)',
    default=float('nan'),
    type=float
)
@click.option(
    '--real-lactate',
    help='the concentration [g / L] of lactic acid if known (default: NaN)',
    default=float('nan'),
    type=float
)
@click.option(
    '--duration',
    help='how many minutes you want to do the recording for (default: 1 min)',
    default=1,
    type=float
)
@click.option(
    '--channel',
    help='where to find the server, i.e. localhost:50051',
    type=str,
    required=True,
)
def record(name, real_glucose, real_lactate, duration, channel):
    click.echo('Start Recording the Sensor for %3d minute(s)' % duration)

    stub = GlucoseSensorStub(grpc.insecure_channel(channel))
    click.echo('Start Monitoring the Sensor for %3d minute(s)' % duration)

    for measurement in stub.record(
            RecordingRequest(
                name=name,
                real_glucose=real_glucose,
                real_lactate=real_lactate,
                duration=duration,
            )
    ):
        click.echo(
            'Time: %s   Glucose: %6.0f nA   Lactate: %6.0f nA' % (
                datetime.datetime.now().isoformat(),
                measurement.glucose_current,
                measurement.lactate_current,
            )
        )

    click.echo('Finished Recording after %3d minute(s)' % duration)


@client.command(help='Start pump from the client')
@click.option(
    '--volume',
    help='desired volume in uL',
    type=float,
    required=True,
)
@click.option(
    '--flow-rate',
    help='desired flow rate (default: 2000 uL / min)',
    type=float,
    default=2000.,
)
@click.option(
    '--channel',
    help='where to find the server, i.e. localhost:50051',
    type=str,
    required=True,
)
def start_pump(volume, flow_rate, channel):
    stub = GlucoseSensorStub(grpc.insecure_channel(channel))
    stub.pump_it_up(
        VolumeRequest(volume=volume, flow_rate=flow_rate)
    )
    click.echo(
        'Send request for volume %4.2E L at %4.2E L / min '
        'flow rate (duration %5.2f sec)' % (
            volume,
            flow_rate,
            volume / flow_rate * 60,
        )
    )


@client.command(help='Monitor the values produced by the sensor')
@click.option(
    '--channel',
    help='where to find the server, i.e. localhost:50051',
    type=str,
    required=True,
)
@click.option(
    '--duration',
    help='how many minutes you want to do the monitoring for (default: 1 min)',
    default=1,
    type=float
)
def monitor(channel, duration):
    stub = GlucoseSensorStub(grpc.insecure_channel(channel))
    click.echo('Start Monitoring the Sensor for %3d minute(s)' % duration)

    for measurement in stub.monitor(MonitoringRequest(duration=duration)):
        click.echo(
            'Time: %s   Glucose: %6.0f nA   Lactate: %6.0f nA' % (
                measurement.timestamp,
                measurement.glucose_current,
                measurement.lactate_current,
            )
        )

    click.echo('Finished Monitoring after %3d minute(s)' % duration)
