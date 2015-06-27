# SwiftingBridge

Apple's Scripting Bridge is totally awesome, but also unfortunately a complete mess. Swift is also fantastic, but still a bit of a mess as it continues to evolve. Here I have created their bastard child.

Swifting Bridge uses Apple's builtin `sdef` and `sdp` utilities to generate a Scripting Bridge header (as described in [Apple's official documentation for Scripting Bridge](https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/ScriptingBridgeConcepts/UsingScriptingBridge/UsingScriptingBridge.html#//apple_ref/doc/uid/TP40006104-CH4-SW1)) and then uses that generated Objective-C header to generate a native Swift file with (theoretically) all of the same functionality. That Swift file can be drug straight into a full Swift application and voila. 

- No Objective-C Bridging Headers.
- No Swift wrappers.
- No dealing with generic `SBObject`s.
- No damn linker errors.
