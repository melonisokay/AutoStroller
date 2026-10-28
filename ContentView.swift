//
//  ContentView.swift
//  UWB-Test
//
//  Created by clemsonuser on 10/28/26.
//

import SwiftUI

struct ContentView: View {
    // Instantiate our unified manager to drive the UI
    @StateObject private var rangingManager = UnifiedRangingManager()

    
    var body: some View {
        VStack(spacing: 30) {
            // Header Card
            VStack(spacing: 8) {
                Image(systemName: "antenna.radiowaves.left.and.right")
                    .font(.system(size: 50))
                    .foregroundColor(.blue)
                
                Text("UWB Telemetry Hub")
                    .font(.title)
                    .fontWeight(.bold)
            }
            .padding(.top, 40)
            
            Spacer()
            
            // Live Ranging Output Display
            VStack(spacing: 12) {
                Text("Distance to Qorvo Anchor")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .textCase(.uppercase)
                
                if rangingManager.currentDistance > 0 {
                    HStack(alignment: .lastTextBaseline, spacing: 4) {
                        Text(String(format: "%.2f", rangingManager.currentDistance))
                            .font(.system(size: 72, weight: .bold, design: .rounded))
                            .foregroundColor(.primary)
                        Text("m")
                            .font(.title)
                            .fontWeight(.semibold)
                            .foregroundColor(.secondary)
                    }
                } else {
                    Text("Awaiting Ranging...")
                        .font(.title2)
                        .foregroundColor(.secondary)
                        .italic()
                }
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(16)
            .shadow(color: Color.black.opacity(0.05), radius: 10, x: 0, y: 5)
            
            Spacer()
            
            // Peripheral Data Pipeline Status Monitor
            VStack(alignment: .leading, spacing: 12) {
                Text("Hardware Integration Status")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.secondary)
                
                // Raspberry Pi Status Indicator
                HStack {
                    Circle()
                        .frame(width: 12, height: 12)
                        .foregroundColor(rangingManager.isPiConnected ? .green : .orange)
                    
                    Text("Raspberry Pi 5 Pipeline:")
                        .font(.body)
                    
                    Spacer()
                    
                    Text(rangingManager.isPiConnected ? "Streaming" : "Scanning...")
                        .font(.body)
                        .fontWeight(.medium)
                        .foregroundColor(rangingManager.isPiConnected ? .green : .orange)
                }
            }
            .padding()
            .background(Color(.secondarySystemBackground))
            .cornerRadius(12)
            
            .padding(.bottom, 20)
        }
        .padding(.horizontal, 24)
        .background(Color(.systemGroupedBackground).edgesIgnoringSafeArea(.all))
    }
}


#Preview {
    ContentView()
}
