graph [
  label "Internet2"
  directed 0
  node [
    id 0
    label "SaltLakeCity"
  ]
  node [
    id 1
    label "LosAngeles"
  ]
  node [
    id 2
    label "Houston"
  ]
  node [
    id 3
    label "KansasCity"
  ]
  node [
    id 4
    label "Chicago"
  ]
  node [
    id 5
    label "Atlanta"
  ]
  node [
    id 6
    label "WashingtonDC"
  ]
  node [
    id 7
    label "Cleveland"
  ]
  node [
    id 8
    label "NewYork"
  ]
  edge [
    source 0
    target 1
    availability 0.9995
    capacity 100.0
  ]
  edge [
    source 0
    target 3
    availability 0.999
    capacity 100.0
  ]
  edge [
    source 1
    target 2
    availability 0.999
    capacity 100.0
  ]
  edge [
    source 2
    target 5
    availability 0.999
    capacity 100.0
  ]
  edge [
    source 3
    target 4
    availability 0.9995
    capacity 100.0
  ]
  edge [
    source 3
    target 2
    availability 0.9985
    capacity 100.0
  ]
  edge [
    source 4
    target 7
    availability 0.9999
    capacity 100.0
  ]
  edge [
    source 4
    target 5
    availability 0.999
    capacity 100.0
  ]
  edge [
    source 5
    target 6
    availability 0.9995
    capacity 100.0
  ]
  edge [
    source 6
    target 7
    availability 0.999
    capacity 100.0
  ]
  edge [
    source 6
    target 8
    availability 0.9999
    capacity 100.0
  ]
  edge [
    source 7
    target 8
    availability 0.9995
    capacity 100.0
  ]
  edge [
    source 0
    target 4
    availability 0.998
    capacity 100.0
  ]
]

