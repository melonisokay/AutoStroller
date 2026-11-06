//
//  UnifiedRangingManager.swift
//  UWB-Test
//
//  Created by clemsonuser on 10/28/26.
//


import Foundation
import NearbyInteraction
import CoreBluetooth
import Combine

class UnifiedRangingManager: NSObject, ObservableObject, NISessionDelegate, CBCentralManagerDelegate, CBPeripheralDelegate {
    
    // Nearby Interaction Properties
    private var niSession: NISession?
    @Published var currentDistance: Float = 0.0
    @Published var isPiConnected: Bool = false
    
    // Raspberry Pi BLE Forwarding Properties
    private var centralManager: CBCentralManager!
    private var piPeripheral: CBPeripheral?
    private var piCharacteristic: CBCharacteristic?
    private var qorvoPeripheral: CBPeripheral?
    private var qorvoRxCharacteristic: CBCharacteristic?
    
    // Replace with your specific Raspberry Pi BLE Service & Characteristic UUIDs
    let PI_SERVICE_UUID = CBUUID(string: "4A98C721-1234-ABCD-EF01-9876543210AB")
    let PI_CHAR_UUID    = CBUUID(string: "4A98C722-1234-ABCD-EF01-9876543210AB")
    
    // Qorvo / Apple Accessory Transfer Service Profile
//    Discovered peripheral -> Name: DWM3001CDK (3711EEC3), LocalName: DWM3001CDK (3711EEC3), UUID: D172C875-9787-2009-8A37-5A18B23933F3
    let QORVO_SERVICE_UUID   = CBUUID(string: "6E400001-B5A3-F393-E0A9-E50E24DCCA9E") // Service
    let QORVO_RX_CHAR_UUID   = CBUUID(string: "6E400002-B5A3-F393-E0A9-E50E24DCCA9E") // iOS Writes to Anchor
    let QORVO_TX_CHAR_UUID   = CBUUID(string: "6E400003-B5A3-F393-E0A9-E50E24DCCA9E") // iOS Reads from Anchor
    
    override init() {
        super.init()
        // Initialize BLE to scan for Raspberry Pi
        self.centralManager = CBCentralManager(delegate: self, queue: nil)
        
        // Start Nearby Interaction Session
        setupNISession()
    }
    
    // MARK: - Nearby Interaction Setup
    private func setupNISession() {
        // Modern capability-based check for precise distance measurement
        let isUWBSupported: Bool = {
            if #available(iOS 16.0, watchOS 9.0, *) {
                return NISession.deviceCapabilities.supportsPreciseDistanceMeasurement
            } else {
                // Fallback for older legacy operating system instances
                return NISession.isSupported
            }
        }()
        
        guard isUWBSupported else {
            print("Precise UWB distance tracking is not supported on this hardware configuration.")
            return
        }
        
        niSession = NISession()
        niSession?.delegate = self
    }
    
    // Handshake configuration data received out-of-band (via Qorvo BLE stack)
    func startUWBRanging(with accessoryData: Data) {
        do {
            // Parse configuration data delivered by Qorvo firmware specification
            let configuration = try NINearbyAccessoryConfiguration(data: accessoryData)
            niSession?.run(configuration)
            print("UWB Ranging initiated with Qorvo Anchor.")
        } catch {
            print("Failed to initialize Qorvo accessory configuration: \(error)")
        }
    }
    
    // MARK: - NISessionDelegate
    func session(_ session: NISession, didUpdate nearbyObjects: [NINearbyObject]) {
        guard let nearbyObject = nearbyObjects.first else { return }
        
        // Grab the precise distance in meters
        if let distance = nearbyObject.distance {
            // CRITICAL: Push this explicitly to the Main Queue so SwiftUI triggers a visual redraw
            DispatchQueue.main.async {
                self.currentDistance = distance
            }
            print("UWB Live Distance: \(distance) meters")
            
            // Immediately forward this data payload over to the Raspberry Pi 5
            forwardDistanceToPi(distance: distance)
        }
    }
    
    
    func session(_ session: NISession, didRemove nearbyObjects: [NINearbyObject], reason: NINearbyObject.RemovalReason) {
        // Handle physical connection or session drops gracefully
        niSession?.invalidate()
        setupNISession()
    }
    
    // MARK: - CoreBluetooth Central Manager Delegate
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            print("CoreBluetooth Online. Phase 1: Initiating global scan to bypass hidden headers...")
            // Passing nil tells iOS to report ALL broadcasting BLE devices nearby
            centralManager.scanForPeripherals(withServices: nil, options: nil)
        }
    }
    
    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String : Any], rssi: NSNumber) {
        // Extract the broadcasting local name string if present
        let localName = advertisementData[CBAdvertisementDataLocalNameKey] as? String ?? "Unknown"
        
        // Check if the device is a Qorvo Anchor by checking common naming formats
        if qorvoPeripheral == nil && localName.contains("DWM3001CDK") {
            print("🎯 Identified Qorvo Anchor by broadcast name signature: \(localName)")
            qorvoPeripheral = peripheral
            qorvoPeripheral?.delegate = self
            
            // Removed stopScan() here to allow the Pi to still be discovered concurrently
            central.connect(peripheral, options: nil)
            return
        }
        
        
        // Phase 2 check (looking for the Pi)
        if piPeripheral == nil, let serviceUUIDs = advertisementData[CBAdvertisementDataServiceUUIDsKey] as? [CBUUID], serviceUUIDs.contains(PI_SERVICE_UUID) {
            print("🎯 Found Raspberry Pi 5 Node.")
            piPeripheral = peripheral
            piPeripheral?.delegate = self
            
            // Removed stopScan() here to allow the Qorvo anchor to still be discovered concurrently
            central.connect(peripheral, options: nil)
        }
    }

    
    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        if peripheral.identifier == qorvoPeripheral?.identifier {
            print("Connected to Qorvo Hardware. Initializing Service Discovery...")
            peripheral.discoverServices([QORVO_SERVICE_UUID])
        } else if peripheral.identifier == piPeripheral?.identifier {
            print("Connected to Raspberry Pi 5 Data Hub.")
            DispatchQueue.main.async {
                self.isPiConnected = true
            }
            peripheral.discoverServices([PI_SERVICE_UUID])
        }
    }
    
    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        if peripheral.identifier == piPeripheral?.identifier {
            print("Raspberry Pi 5 disconnected.")
            DispatchQueue.main.async {
                self.isPiConnected = false
            }
            piPeripheral = nil
            piCharacteristic = nil
            // Scan specifically to recover the Pi channel
            centralManager.scanForPeripherals(withServices: [PI_SERVICE_UUID], options: nil)
        } else if peripheral.identifier == qorvoPeripheral?.identifier {
            print("❌ Qorvo Anchor connection lost. Resetting core tracking...")
            qorvoPeripheral = nil
            qorvoRxCharacteristic = nil
            niSession?.invalidate()
            setupNISession()
            // Reset system to look for the anchor again
            centralManager.scanForPeripherals(withServices: [QORVO_SERVICE_UUID], options: nil)
        }
    }
    
    
    // MARK: - CBPeripheralDelegate
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let services = peripheral.services else { return }
        for service in services {
            if service.uuid == PI_SERVICE_UUID {
                peripheral.discoverCharacteristics([PI_CHAR_UUID], for: service)
            } else if service.uuid == QORVO_SERVICE_UUID {
                peripheral.discoverCharacteristics([QORVO_RX_CHAR_UUID, QORVO_TX_CHAR_UUID], for: service)
            }
        }
    }
    
    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard let characteristics = service.characteristics else { return }
        for characteristic in characteristics {
            if characteristic.uuid == PI_CHAR_UUID {
                self.piCharacteristic = characteristic
                print("BLE pipeline upstream to Raspberry Pi verified.")
            } else if characteristic.uuid == QORVO_RX_CHAR_UUID {
                self.qorvoRxCharacteristic = characteristic
            } else if characteristic.uuid == QORVO_TX_CHAR_UUID {
                // Subscribe to incoming configuration token updates from the anchor
                peripheral.setNotifyValue(true, for: characteristic)
                print("Subscribed to Qorvo Telemetry Token channel.")
            }
        }
    }
    
    // MARK: - CBPeripheralDelegate
    // All raw bluetooth incoming packets flow through here inside the manager
    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        if characteristic.uuid == QORVO_TX_CHAR_UUID {
            guard let rawData = characteristic.value else { return }
            
            // CRITICAL FOR QANI FW: Verify and extract the Apple payload
            if rawData.first == 0x01 {
                print("QANI Accessory Token Received (\(rawData.count) bytes). Stripping Qorvo wrapper...")
                
                // Drop the 0x01 identifier byte to isolate the pure Apple-compliant configuration block
                let cleanAppleConfigData = rawData.dropFirst()
                
                // Pass the verified data to Nearby Interaction
                self.startUWBRanging(with: cleanAppleConfigData)
                
                // Forward the raw byte stream directly to the Raspberry Pi pipeline
                if let piPeripheral = self.piPeripheral, let piChar = self.piCharacteristic {
                    // Write using .withoutResponse for continuous high-speed streaming
                    piPeripheral.writeValue(rawData, for: piChar, type: .withoutResponse)
                } else {
                    print("⚠️ Cannot forward data: Pi pipeline is not connected or verified yet.")
                }
            } else {
                print("Received unexpected packet structure from QANI firmware.")
            }
        }
    }
    
    
    // MARK: - NISessionDelegate (The Bidirectional Loop)
    func session(_ session: NISession, didGenerateShareableConfigurationData shareableConfigurationData: Data, for object: NINearbyObject) {
        guard let qorvoPeripheral = qorvoPeripheral, let rxCharacteristic = qorvoRxCharacteristic else { return }
        
        var outboundPayload = Data([0x02])
        outboundPayload.append(shareableConfigurationData)
        
        qorvoPeripheral.writeValue(outboundPayload, for: rxCharacteristic, type: .withResponse)
        print("UWB handshake token sent to QANI stack.")
        
        // Kick off Phase 2: Look for the Pi 5 now that UWB is up and running
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            guard let self = self else { return }
            if self.piPeripheral == nil {
                print("Phase 2: Initiating background scan for Raspberry Pi 5...")
                self.centralManager.scanForPeripherals(withServices: [self.PI_SERVICE_UUID], options: nil)
            }
        }
    }
    
    
    // MARK: - Forwarding Mechanism
    private func forwardDistanceToPi(distance: Float) {
        guard let peripheral = piPeripheral, let characteristic = piCharacteristic else {
            return // Pi connection not ready yet
        }
        
        // Convert the Float metric value directly into raw Data binary representation
        var mutableDistance = distance
        let payload = Data(bytes: &mutableDistance, count: MemoryLayout<Float>.size)
        
        // Write without response for minimized transmission latency overhead
        peripheral.writeValue(payload, for: characteristic, type: .withoutResponse)
    }
}
