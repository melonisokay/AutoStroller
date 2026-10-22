/* UWB_Tracker.swift
*  ECE 4960 Team 7
*  Sam Gue, Lydia Heath, Gabriel Ruiz, Marilyn Turner, and Sabrina Weng
*
*  Purpose: This file contains code necessary for an iOS application that reads distance from a
*  paired DWM3001CDK using the Nearby Interaction protocol and transmits that information via BLE
*  to a paired Raspberry Pi 5.
*/

import Foundation
import CoreBluetooth
import NearbyInteraction

final class DistanceBLEManager: NSObject, ObservableObject {
    // Must match the UUIDs used by the Raspberry Pi server.
    private let serviceUUID = CBUUID(
        string: "7A1E0001-1234-5678-1234-56789ABCDEF0"
    )
    private let characteristicUUID = CBUUID(
        string: "7A1E0002-1234-5678-1234-56789ABCDEF0"
    )

    private var central: CBCentralManager!
    private var pi: CBPeripheral?
    private var distanceCharacteristic: CBCharacteristic?

    @Published var status = "Initializing Bluetooth"
    @Published var lastDistance: Float?

    override init() {
        super.init()
        central = CBCentralManager(
            delegate: self,
            queue: .main
        )
    }

    func sendDistance(_ meters: Float) {
        guard meters.isFinite, meters >= 0 else { return }

        DispatchQueue.main.async {
            self.lastDistance = meters
        }

        guard let pi = pi,
              let characteristic = distanceCharacteristic else {
            status = "Waiting for Raspberry Pi BLE connection"
            return
        }

        let message: [String: Any] = [
            "distance_m": Double(meters),
            "timestamp": Date().timeIntervalSince1970
        ]

        guard let data = try? JSONSerialization.data(
            withJSONObject: message
        ) else {
            status = "JSON encoding failed"
            return
        }

        let writeType: CBCharacteristicWriteType =
            characteristic.properties.contains(.write)
            ? .withResponse
            : .withoutResponse

        guard writeType == .withResponse ||
              characteristic.properties.contains(.writeWithoutResponse)
        else {
            status = "Characteristic is not writable"
            return
        }

        pi.writeValue(data, for: characteristic, type: writeType)
        status = String(format: "Sent %.2f m", meters)
    }

    func disconnect() {
        if let pi = pi {
            central.cancelPeripheralConnection(pi)
        }
    }
}

extension DistanceBLEManager: CBCentralManagerDelegate {
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        guard central.state == .poweredOn else {
            status = "Bluetooth unavailable: \(central.state.rawValue)"
            return
        }

        status = "Scanning for Raspberry Pi"
        central.scanForPeripherals(
            withServices: [serviceUUID],
            options: [CBCentralManagerScanOptionAllowDuplicatesKey: false]
        )
    }

    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        pi = peripheral
        pi?.delegate = self
        central.stopScan()
        central.connect(peripheral, options: nil)
        status = "Connecting to Raspberry Pi"
    }

    func centralManager(
        _ central: CBCentralManager,
        didConnect peripheral: CBPeripheral
    ) {
        status = "Connected; discovering service"
        peripheral.discoverServices([serviceUUID])
    }

    func centralManager(
        _ central: CBCentralManager,
        didFailToConnect peripheral: CBPeripheral,
        error: Error?
    ) {
        status = "Connection failed"
        pi = nil
        distanceCharacteristic = nil
        central.scanForPeripherals(
            withServices: [serviceUUID],
            options: nil
        )
    }

    func centralManager(
        _ central: CBCentralManager,
        didDisconnectPeripheral peripheral: CBPeripheral,
        error: Error?
    ) {
        pi = nil
        distanceCharacteristic = nil
        status = "Disconnected; scanning again"
        central.scanForPeripherals(
            withServices: [serviceUUID],
            options: nil
        )
    }
}

extension DistanceBLEManager: CBPeripheralDelegate {
    func peripheral(
        _ peripheral: CBPeripheral,
        didDiscoverServices error: Error?
    ) {
        guard error == nil,
              let service = peripheral.services?.first(where: {
                  $0.uuid == serviceUUID
              }) else {
            status = "BLE service not found"
            return
        }

        peripheral.discoverCharacteristics(
            [characteristicUUID],
            for: service
        )
    }

    func peripheral(
        _ peripheral: CBPeripheral,
        didDiscoverCharacteristicsFor service: CBService,
        error: Error?
    ) {
        guard error == nil,
              let characteristic = service.characteristics?.first(where: {
                  $0.uuid == characteristicUUID
              }) else {
            status = "Writable characteristic not found"
            return
        }

        distanceCharacteristic = characteristic
        status = "Ready to transmit distance"
    }

    func peripheral(
        _ peripheral: CBPeripheral,
        didWriteValueFor characteristic: CBCharacteristic,
        error: Error?
    ) {
        if let error = error {
            status = "BLE write failed: \(error.localizedDescription)"
        } else {
            status = "Distance delivered to BLE characteristic"
        }
    }
}
