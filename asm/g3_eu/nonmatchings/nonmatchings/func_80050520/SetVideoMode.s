.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching SetVideoMode, 0x18

glabel SetVideoMode
    /* 30D20 80050520 0980023C */  lui        $v0, %hi(video_mode)
    /* 30D24 80050524 046C428C */  lw         $v0, %lo(video_mode)($v0)
    /* 30D28 80050528 0980013C */  lui        $at, %hi(video_mode)
    /* 30D2C 8005052C 046C24AC */  sw         $a0, %lo(video_mode)($at)
    /* 30D30 80050530 0800E003 */  jr         $ra
    /* 30D34 80050534 00000000 */   nop
endlabel SetVideoMode
