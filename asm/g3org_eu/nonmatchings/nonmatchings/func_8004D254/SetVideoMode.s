.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching SetVideoMode, 0x18

glabel SetVideoMode
    /* 2DA54 8004D254 0A80023C */  lui        $v0, %hi(video_mode)
    /* 2DA58 8004D258 1039428C */  lw         $v0, %lo(video_mode)($v0)
    /* 2DA5C 8004D25C 0A80013C */  lui        $at, %hi(video_mode)
    /* 2DA60 8004D260 103924AC */  sw         $a0, %lo(video_mode)($at)
    /* 2DA64 8004D264 0800E003 */  jr         $ra
    /* 2DA68 8004D268 00000000 */   nop
endlabel SetVideoMode
