//
//  ContentView.swift
//  UWB AutoStroller
//
//  Created by Lydia Heath on 10/23/26.
//

// import SwiftData
import SwiftUI

struct ContentView: View {
    @Environment(UWBBluetoothManager.self) private var manager
    
    var body: some View {
        VStack(spacing: 20) {
            Text("UWB AutoStroller Controller")
                .font(.headline)
            
            Text(manager.bluetoothStatus)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            if let distance = manager.currentDistance {
                Text(String(format: "%.2f meters", distance))
                    .font(.system(size: 42, weight: .bold, design: .rounded))
                    .foregroundColor(.blue)
            } else {
                Text("---")
                    .font(.system(size: 42, weight: .bold, design: .rounded))
                    .foregroundColor(.gray)
            }
        }
        .padding()
    }
}
