# Vertex AI Region Configuration for Claude Models

## Issue

Claude models on Vertex AI are not available in all regions. If you see an error like:

```
Publisher Model `projects/.../locations/us-central1/publishers/anthropic/models/claude-sonnet-4-5@20250929` is not servable in region us-central1.
```

This means the model is not available in that region.

## Supported Regions

Claude models on Vertex AI are typically available in these regions:

- **us-east4** (Virginia) - ✅ Recommended
- **us-west1** (Oregon) - ✅ Recommended  
- **us-central1** (Iowa) - ❌ May not support Claude models
- **europe-west1** (Belgium) - Check availability
- **asia-northeast1** (Tokyo) - Check availability

## How to Change Region

### Option 1: Update .env file

Edit `sdlc-agent-framework/.env`:

```bash
# Change from:
CLOUD_ML_REGION=us-central1

# To:
CLOUD_ML_REGION=us-east4
```

### Option 2: Use Environment Variable

```bash
export CLOUD_ML_REGION=us-east4
```

## Verify Region Availability

To check if Claude models are available in a region:

```bash
# List available models in a region
gcloud ai models list \
  --region=us-east4 \
  --project=agents-with-claude \
  --filter="displayName:claude"

# Or check via Vertex AI API
gcloud ai endpoints list \
  --region=us-east4 \
  --project=agents-with-claude
```

## Current Configuration

Check your current region:

```bash
cd sdlc-agent-framework
grep CLOUD_ML_REGION .env
```

## Testing After Region Change

After changing the region, test again:

```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 scripts/test_vertex_ai_agent.py
```

## Additional Notes

- Region changes take effect immediately (no restart needed)
- Different regions may have different pricing
- Latency may vary by region
- Some regions may require approval for Claude model access

## Troubleshooting

If you still get region errors:

1. **Check model availability**: Verify Claude models are available in your chosen region
2. **Try alternative regions**: Test with `us-east4` or `us-west1`
3. **Check project permissions**: Ensure your project has access to Claude models
4. **Verify billing**: Ensure billing is enabled for the project
5. **Check quotas**: Verify you haven't exceeded regional quotas

## References

- [Vertex AI Regions](https://cloud.google.com/vertex-ai/docs/general/locations)
- [Anthropic Claude on Vertex AI](https://cloud.google.com/vertex-ai/docs/model-garden/anthropic)

