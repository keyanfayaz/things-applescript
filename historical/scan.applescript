use AppleScript version "2.5"
use framework "Foundation"
use scripting additions

-- Explicit read-only property requests only. Never request properties, notes,
-- private JSON, task changes, UI commands, or Things' database files.
-- List IDs were discovered through Things' public scripting interface.

on dictionary()
    return current application's NSMutableDictionary's alloc()'s init()
end dictionary

on array()
    return current application's NSMutableArray's alloc()'s init()
end array

on listSummary(listID, titleLimit)
    set resultDict to my dictionary()
    set titles to my array()
    tell application id "com.culturedcode.ThingsMac"
        set sourceList to list id listID
        set listName to name of sourceList
        set totalCount to count of to dos of sourceList
        set readCount to totalCount
        if readCount > titleLimit then set readCount to titleLimit
        repeat with taskIndex from 1 to readCount
            set taskTitle to name of to do taskIndex of sourceList
            titles's addObject:taskTitle
        end repeat
    end tell
    resultDict's setObject:listID forKey:"id"
    resultDict's setObject:listName forKey:"name"
    resultDict's setObject:totalCount forKey:"total_count"
    resultDict's setObject:readCount forKey:"returned_count"
    resultDict's setObject:titles forKey:"titles"
    resultDict's setObject:(current application's NSNumber's numberWithBool:(totalCount > readCount)) forKey:"truncated"
    return resultDict
end listSummary

on run
    set resultDict to my dictionary()
    set areaRows to my array()
    set projectRows to my array()
    with timeout of 60 seconds
        tell application id "com.culturedcode.ThingsMac"
            set appVersion to version
            repeat with areaRef in every area
                set areaRow to my dictionary()
                areaRow's setObject:(id of areaRef) forKey:"id"
                areaRow's setObject:(name of areaRef) forKey:"name"
                areaRow's setObject:(count of to dos of areaRef) forKey:"task_count"
                areaRows's addObject:areaRow
            end repeat
            repeat with projectRef in every project
                set projectRow to my dictionary()
                projectRow's setObject:(id of projectRef) forKey:"id"
                projectRow's setObject:(name of projectRef) forKey:"name"
                projectRow's setObject:((status of projectRef) as text) forKey:"status"
                projectRow's setObject:(count of to dos of projectRef) forKey:"task_count"
                set parentArea to area of projectRef
                set parentID to ""
                set parentName to ""
                if parentArea is not missing value then
                    set parentID to id of parentArea
                    set parentName to name of parentArea
                end if
                projectRow's setObject:parentID forKey:"area_id"
                projectRow's setObject:parentName forKey:"area_name"
                projectRows's addObject:projectRow
            end repeat
        end tell
        set inboxRow to my listSummary("TMInboxListSource", 30)
        set todayRow to my listSummary("TMTodayListSource", 30)
    end timeout
    resultDict's setObject:appVersion forKey:"app_version"
    resultDict's setObject:"com.culturedcode.ThingsMac" forKey:"bundle_id"
    resultDict's setObject:"read-only areas/projects and up to 30 Inbox/Today titles; notes excluded" forKey:"scope"
    resultDict's setObject:areaRows forKey:"areas"
    resultDict's setObject:projectRows forKey:"projects"
    resultDict's setObject:inboxRow forKey:"inbox"
    resultDict's setObject:todayRow forKey:"today"
    set jsonData to current application's NSJSONSerialization's dataWithJSONObject:resultDict options:1 |error|:(missing value)
    if jsonData is missing value then error "JSON serialization failed"
    set jsonText to current application's NSString's alloc()'s initWithData:jsonData encoding:(current application's NSUTF8StringEncoding)
    return jsonText as text
end run
