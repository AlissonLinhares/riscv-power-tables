/*======================================================================*/
/* Proxy kernel linker script                                           */
/*======================================================================*/
/* This is the linker script used when building the proxy kernel. */

/*----------------------------------------------------------------------*/
/* Setup                                                                */
/*----------------------------------------------------------------------*/

/* The OUTPUT_ARCH command specifies the machine architecture where the
   argument is one of the names used in the BFD library. More
   specifically one of the entires in bfd/cpu-mips.c */

OUTPUT_ARCH( "riscv" )

/*----------------------------------------------------------------------*/
/* Sections                                                             */
/*----------------------------------------------------------------------*/

SECTIONS
{
  /* River's jump address */
  . = 0x0000;

  /* Test code section */
  .text : ALIGN(512) {
    *(.text)
  }

  /* Read-only data, aligned after text section. */
  .rodata : ALIGN(512) {
    *(.rodata)
  }

  /* River's ram address */
  . = 0x10000000;

  /* data region for elf testing */
  .data : {
    *(.data)
    . += 0x80000;
  }
}
