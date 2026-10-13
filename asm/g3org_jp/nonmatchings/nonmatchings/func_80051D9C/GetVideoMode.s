.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching GetVideoMode, 0x10

glabel GetVideoMode
    /* 3259C 80051D9C 0A80023C */  lui        $v0, %hi(video_mode)
    /* 325A0 80051DA0 9843428C */  lw         $v0, %lo(video_mode)($v0)
    /* 325A4 80051DA4 0800E003 */  jr         $ra
    /* 325A8 80051DA8 00000000 */   nop
endlabel GetVideoMode
