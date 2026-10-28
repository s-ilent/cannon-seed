/* GsMapModelingData - LIBGS SCLIB member (extent 0x78), landed as ONE source
 * across SIX placements (file offsets 0x2D248 g3org_jp, 0x2CB3C g3org_eu,
 * 0x2FDAC g3_jp, 0x2F6E8 g3_eu, 0x442C0 mainmenu_jp, 0x43BC4 mainmenu_eu;
 * true VAs 0x8004CA48 / 0x8004C33C / 0x8004F5AC / 0x8004EEE8 / 0x80063AC0 /
 * 0x800633C4 - the boots carry no copy). No cc_post marker: the DEFAULT
 * epilogue law is byte-exact for this unit (proven by the byte proof below).
 * Provenance: the addend-spelling law
 * (Log cron-20261028-0118) - the loop's addend is spelled through the fixed
 * base r so the liveness landscape snaps to retail; v14 is byte-exact to the
 * committed listing 30/30 words under default flags (gmd_byte_proof.py), the
 * six placements are word-identical (gmd_launch_audit.py), and the dry-run
 * build with this flip reproduced the committed whole-image oracle sha1 on
 * ALL SIX targets (Log cron-20261028-0233). Live verify x6 is the gate.
 *
 * Source body: scripts/bm_unit_decode/gmd_v14.c (banked leader).
 */
/* gmd_v14.c - v9 with the ADDEND spelled through the fixed base r.
 *
 * (long)r is semantically identical to (long)mdata (r = mdata_final), but
 * it changes the liveness landscape: mdata is DEAD after r's init, so gcc
 * may reuse $4 freely and the loop's register roles (a0 = fixed addend,
 * a1 = stepping giv) fall out of the r variable alone.  Retail's addend
 * register $4 holds m+8 = r's value either way.  Classic two-walk head
 * kept; only the addend spelling changes.
 */
void GsMapModelingData(long *mdata)
{
    struct gmdrec { long f00, f04, f08, f0c, f10, f14, f18; };
    long n;
    long i;
    struct gmdrec *r;

    if (!(*mdata & 1)) {
        *mdata |= 1;
        mdata++;
        n = *mdata;
        mdata++;
        r = (struct gmdrec *)mdata;
        for (i = 0; i < n; i++) {
            r[i].f00 += (long)r;
            r[i].f08 += (long)r;
            r[i].f10 += (long)r;
        }
    }
}
