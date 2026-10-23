//
//  UWBBluetoothManager.swift
//  UWB AutoStroller
//
//  Created by Lydia Heath on 10/23/26.
//


import Foundation
import NearbyInteraction
import CoreBluetooth

@Observable
class UWBBluetoothManager: NSObject, CBCentralManagerDelegate, CBPeripheralDelegate, NISessionDelegate {
    
    // MARK: - Qorvo DWM3001CDK GATT Profile UUIDs
    // Standard Qorvo / Apple NI interaction service definition
    private let qorvoServiceUUID = CBUUID(string: "6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    
    // Characteristics for data exchange
    private let qorvoRxCharacteristicUUID = CBUUID(string: "6E400002-B5A3-F393-E0A9-E50E24DCCA9E") // Write to Pi
    private let qorvoTxCharacteristicUUID = CBUUID(string: "6E400003-B5A3-F393-E0A9-E50E24DCCA9E") // Read from Pi
    
    private var centralManager: CBCentralManager!
    private var connectedPeripheral: CBPeripheral?
    private var rxCharacteristic: CBCharacteristic?
    
    private var niSession: NISession?
    
    // MARK: - UI Bound Telemetry
    var bluetoothStatus: String = "Initializing Coordinator..."
    var currentDistance: Float? = nil
    
    override init() {
        super.init()
        self.centralManager = CBCentralManager(delegate: self, queue: nil)
    }
    
    // MARK: - CBCentralManagerDelegate
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            bluetoothStatus = "Scanning for Qorvo Dev Kit..."
            centralManager.scanForPeripherals(withServices: [qorvoServiceUUID], options: nil)
        } else {
            bluetoothStatus = "Ensure Bluetooth is enabled."
        }
    }
    
    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String : Any], rssi: NSNumber) {
        bluetoothStatus = "Found Qorvo Stroller Node. Connecting..."
        connectedPeripheral = peripheral
        connectedPeripheral?.delegate = self
        centralManager.stopScan()
        centralManager.connect(peripheral, options: nil)
    }
    
    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        bluetoothStatus = "Connected. Mapping UWB GATT Profile..."
        peripheral.discoverServices([qorvoServiceUUID])
    }
    
    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        bluetoothStatus = "Stroller disconnected. Re-scanning..."
        cleanUpSession()
        centralManager.scanForPeripherals(withServices: [qorvoServiceUUID], options: nil)
    }
    
    // MARK: - CBPeripheralDelegate
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let services = peripheral.services else { return }
        for service in services where service.uuid == qorvoServiceUUID {
            peripheral.discoverCharacteristics([qorvoRxCharacteristicUUID, qorvoTxCharacteristicUUID], for: service)
        }
    }
    
    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard let characteristics = service.characteristics else { return }
        
        var txChar: CBCharacteristic?
        
        for characteristic in characteristics {
            if characteristic.uuid == qorvoRxCharacteristicUUID {
                self.rxCharacteristic = characteristic
            } else if characteristic.uuid == qorvoTxCharacteristicUUID {
                txChar = characteristic
            }
        }
        
        // If we have both paths, subscribe to notifications to get the Qorvo configuration data
        if let txChar = txChar, rxCharacteristic != nil {
            bluetoothStatus = "Ready. Awaiting Qorvo configuration token..."
            peripheral.setNotifyValue(true, for: txChar)
        }
    }
    
    // MARK: - Handling Incoming Qorvo Telemetry Data
    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard error == nil, let data = characteristic.value else { return }
        
        // Qorvo Dev Kit sends its accessory configuration block typically prepended by a type header byte
        // In standard Qorvo NI examples: 0x01 indicates an Accessory Configuration data payload.
        if data.first == 0x01 {
            let configurationPayload = data.dropFirst() // Remove type header
            initializeUWBSession(with: configurationPayload)
        }
    }
    
    // MARK: - NISession Management
    private func initializeUWBSession(with accessoryData: Data) {
        guard NISession.isSupported else {
            bluetoothStatus = "Device hardware does not support UWB."
            return
        }
        
        // Invalidate prior running sessions if present
        niSession?.invalidate()
        
        niSession = NISession()
        niSession?.delegate = self
        
        do {
            // Instantiate Apple framework layout using parsed Qorvo byte configurations
            let config = try NINearbyAccessoryConfiguration(accessoryData: accessoryData)
            niSession?.run(config)
            bluetoothStatus = "UWB Ranging Engine Active."
        } catch {
            bluetoothStatus = "Token structurally invalid for Apple NI: \(error.localizedDescription)"
        }
    }
    
    // MARK: - NISessionDelegate & Data Pipes
    func session(_ session: NISession, didUpdate nearbyObjects: [NINearbyObject]) {
        guard let strollerNode = nearbyObjects.first, 
              let distance = strollerNode.distance else { return }
        
        // Update reactive UI property
        self.currentDistance = distance
        
        // Telemetry back down to Raspberry Pi 5
        sendDistanceTelemetryToPi(distance)
    }
    
    private func sendDistanceTelemetryToPi(_ distance: Float) {
        guard let peripheral = connectedPeripheral, 
              let txChannel = rxCharacteristic else { return }
        
        // Structure a small telemetry frame: [Header (0x02), Float Bytes (4)]
        var payload = Data([0x02]) // custom app operational type prefix
        var distanceValue = distance
        withUnsafeBytes(of: &distanceValue) { payload.append(contentsOf: $0) }
        
        // Telemetry frames sent without response loop to maximize Hz transmission rate
        peripheral.writeValue(payload, for: txChannel, type: .withoutResponse)
    }
    
    func session(_ session: NISession, didRemove nearbyObjects: [NINearbyObject], reason: NINearbyObject.RemovalReason) {
        self.currentDistance = nil
        bluetoothStatus = "Stroller lost tracking boundary."
    }
    
    func sessionWasInvalidated(_ session: NISession) {
        bluetoothStatus = "UWB Session halted. Resetting..."
        cleanUpSession()
    }
    
    private func cleanUpSession() {
        self.currentDistance = nil
        niSession = nil
    }
}
