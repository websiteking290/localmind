# LocalMind Mass Production Guide

## Overview
This guide covers everything needed to manufacture and sell LocalMind USB drives at scale.

## Components per Unit

### Hardware
- **USB Drive**: SanDisk Ultra Dual Drive USB-C 128GB (SDDDC4-128G-G46)
  - Read: 400 MB/s, Write: 150 MB/s
  - USB-C + USB-A dual connector
  - Cost: ~$18/unit at 100+ qty
  - Source: Amazon Business, Ingram Micro, CDW

### Packaging
- **Box**: 3.5" x 2.5" x 0.75" custom printed cardboard
  - Cost: ~$2/unit at 500+ qty
  - Source: Packhelp, Packlane
- **Insert**: Instruction card + warranty info
  - Cost: ~$0.50/unit
- **Label**: Sticker on USB with LocalMind logo
  - Cost: ~$0.25/unit

### Software (Pre-installed)
- Ollama engine (Windows + macOS + Linux binaries)
- 5 AI models (~24 GB)
- LocalMind launcher + dashboard
- Update system
- User data partition (~100 GB free)

## Production Workflow

### 1. Master Image Creation
```bash
# Run on a Linux build machine
cd /path/to/LocalMind
./scripts/create-disk-image.sh
```
This creates:
- `localmind-128gb.img` — raw disk image
- `localmind-128gb.zip` — compressed for distribution
- `flash.sh` — Linux/Mac flashing tool
- `flash.ps1` — Windows flashing tool

### 2. Master Drive Preparation
1. Insert a fresh 128GB SanDisk USB
2. Flash master image:
   ```bash
   sudo ./flash.sh /dev/sdX
   ```
3. Verify on Windows and macOS
4. Label as "MASTER — DO NOT SELL"

### 3. Bulk Duplication

#### Option A: USB Duplicator (Recommended for 100+)
- **1-to-7**: EZ Dupe 7 Target (~$400)
  - 7 drives every 5 minutes
  - ~80 drives/hour
  
- **1-to-15**: Kanguru USB Duplicator (~$1,200)
  - 15 drives every 5 minutes
  - ~180 drives/hour

#### Option B: Software Duplication (Small batches)
```bash
# On Linux/Mac
for dev in /dev/sdb /dev/sdc /dev/sdd; do
  sudo dd if=localmind-128gb.img of=$dev bs=4M status=progress
done
```

### 4. Quality Control
- Spot-check 1 in 10 drives
- Verify on both Windows and macOS
- Check all 5 models load correctly
- Test launcher opens dashboard

### 5. Packaging
1. Apply label sticker to USB
2. Insert USB into box
3. Add instruction card
4. Seal box with shrink wrap (optional)

## Fulfillment

### Shipping
- **Weight**: ~1 oz per unit
- **US Shipping**: USPS First Class ($4-6, 3-5 days)
- **International**: USPS First Class International ($10-15, 7-21 days)
- **Tracking**: Included for US, optional for international

### Packaging for Shipping
- Individual box in padded envelope (bubble mailer)
- Cost: ~$0.50/unit

## Cost Breakdown (at 100 units)

| Item | Cost/Unit |
|------|-----------|
| 128GB SanDisk USB | $18.00 |
| Printed box | $2.00 |
| Insert card | $0.50 |
| USB label | $0.25 |
| Shipping materials | $0.50 |
| US shipping (included) | $5.00 |
| **Total COGS** | **$26.25** |
| **Price** | **$129.00** |
| **Margin** | **$102.75 (80%)** |

## Sales Channels

### 1. Direct (Highest Margin)
- Website: localmind.ai
- Payment: Stripe (2.9% + $0.30)
- Net per unit: ~$99

### 2. Amazon FBA
- Amazon fees: ~15%
- FBA fulfillment: ~$5/unit
- Net per unit: ~$85
- Advantage: Prime shipping, trust

### 3. Retail / Wholesale
- Wholesale price: $65/unit (50% off retail)
- Minimum order: 50 units
- Net per unit: ~$39

## Order Fulfillment Workflow

1. **Order received** (website/Amazon)
2. **Pick USB** from inventory
3. **Pack** in mailer with insert
4. **Print label** (ShipStation/Amazon)
5. **Drop off** at USPS
6. **Mark shipped** (auto-tracking email)

## Inventory Management

### Initial Stock Recommendation
- **50 units**: $1,312 COGS
- **100 units**: $2,625 COGS
- **200 units**: $5,250 COGS

### Reorder Point
- Reorder when stock hits 20 units
- Lead time: 2 weeks (USB delivery + duplication)

## Support

### Common Issues
1. **"Python not found"** → Direct to python.org/downloads
2. **"Slow responses"** → Explain CPU-based inference
3. **"Model won't load"** → Check disk space, re-download
4. **"Can't find USB"** → Try different port, check File Explorer

### Support Channels
- Email: support@localmind.ai
- FAQ on website
- Community Discord (optional)

## Warranty & Returns

### 30-Day Money-Back Guarantee
- Full refund, no questions asked
- Customer pays return shipping
- Refund issued within 3 business days

### 1-Year Hardware Warranty
- Defective USB replaced free
- Customer ships defective unit back
- Replacement shipped within 5 business days

## Legal

### Required Disclosures
- AI models are open-source (various licenses)
- Ollama is MIT licensed
- LocalMind launcher/dashboard is MIT licensed
- No warranty on AI output accuracy
- Not responsible for misuse

### Packaging Text Required
- "AI models run locally on your CPU"
- "No internet required after setup"
- "Results may vary based on hardware"
- "30-day money-back guarantee"
- "1-year hardware warranty"

## Marketing

### Key Messages
- "Your AI, offline" — privacy
- "$129 once, not $20/month" — savings vs ChatGPT
- "Plug and play" — ease of use
- "5 models, one price" — value

### Target Audiences
1. **Privacy-conscious users** (journalists, activists, lawyers)
2. **Offline workers** (field researchers, travelers)
3. **Cost-sensitive** (students, small businesses)
4. **AI enthusiasts** (tinkerers, early adopters)

---

**Ready to launch?**
1. Order 50 USB drives
2. Flash master image
3. Duplicate batch
4. Set up Stripe
5. Publish website
6. Start selling!
