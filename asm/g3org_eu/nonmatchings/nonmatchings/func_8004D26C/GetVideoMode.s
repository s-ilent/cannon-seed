.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching GetVideoMode, 0x10

glabel GetVideoMode
    /* 2DA6C 8004D26C 0A80023C */  lui        $v0, %hi(video_mode)
    /* 2DA70 8004D270 1039428C */  lw         $v0, %lo(video_mode)($v0)
    /* 2DA74 8004D274 0800E003 */  jr         $ra
    /* 2DA78 8004D278 00000000 */   nop
endlabel GetVideoMode
