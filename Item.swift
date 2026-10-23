//
//  Item.swift
//  UWB AutoStroller
//
//  Created by Lydia Heath on 10/23/26.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
