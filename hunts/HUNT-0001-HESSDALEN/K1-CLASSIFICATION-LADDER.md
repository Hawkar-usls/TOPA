# K1 Classification Ladder

Each detected track must stop at the lowest class supported by the raw data.

```text
KNOWN / MATCHED
  STAR_OR_PLANET
  SATELLITE_OR_SPACECRAFT
  AIRCRAFT
  METEOR
  BIRD_OR_INSECT
  LENS_OR_INTERNAL_REFLECTION
  H264_OR_CODEC_ARTIFACT
  STACKING_ARTIFACT

UNCERTAIN
  OTHER_CONVENTIONAL_OR_UNCERTAIN

RESIDUAL
  RESIDUAL_UNCLASSIFIED
```

`RESIDUAL_UNCLASSIFIED` means only that the frozen tests did not classify the event. It is not a paranormal, extraterrestrial, or new-physics label.
