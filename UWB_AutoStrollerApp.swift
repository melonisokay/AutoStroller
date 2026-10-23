//
//  UWB_AutoStrollerApp.swift
//  UWB AutoStroller
//
//  Created by Lydia Heath on 10/23/26.
//

import SwiftUI
import SwiftData

@main
struct UWB_AutoStrollerApp: App {
    // Instantiate our custom central coordinator
    @State private var uwbManager = UWBBluetoothManager()
    
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            Item.self,
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        do {
            return try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(uwbManager) // Pass to views
        }
        .modelContainer(sharedModelContainer)
    }
}
