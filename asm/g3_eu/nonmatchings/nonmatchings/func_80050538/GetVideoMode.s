.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching GetVideoMode, 0x10

glabel GetVideoMode
    /* 30D38 80050538 0980023C */  lui        $v0, %hi(video_mode)
    /* 30D3C 8005053C 046C428C */  lw         $v0, %lo(video_mode)($v0)
    /* 30D40 80050540 0800E003 */  jr         $ra
    /* 30D44 80050544 00000000 */   nop
endlabel GetVideoMode
