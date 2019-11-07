# Merge DL files

This process merges the DL output into one file.

It merges the output up to the 3D reco stage.

Included is output from:

| process     | info includes |
| ----------- | ------------- |
| tagger      | croi, precut results, tagger output |
| sparsessnet | track/shower images, sparseimage holding 5-class output |
| vertexer    | candidate vertices, ana trees |
| tracker     | tracks for each vertex with and without space-charge corrections, ana trees |
| shower reco | shower reconstruction, shape analysis of showers |