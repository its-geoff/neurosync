`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 11/11/2025 10:50:31 PM
// Design Name: 
// Module Name: uartrx
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

module UART_RX
    #(parameter CLKS_PER_BIT = 868)
    (
     input          i_Clock,
     input          i_RX_Serial,
     output         o_RX_DV,      //data valid
     output [7:0]   o_RX_Byte
    );

  //State Machine parameters
  localparam IDLE          = 3'b000;
  localparam RX_START_BIT  = 3'b001;
  localparam RX_DATA_BITS  = 3'b010;
  localparam RX_STOP_BIT   = 3'b011;
  localparam CLEANUP       = 3'b100;

  //Make counter wide enough for CLKS_PER_BIT (~868)
  reg [15:0]  r_Clock_Count = 0;
  reg [2:0]   r_Bit_Index   = 0;     //0-7
  reg [7:0]   r_RX_Byte     = 0;
  reg         r_RX_DV       = 0;
  reg [2:0]   r_SM_Main     = IDLE;

  //Drive outputs from internal regs
  assign o_RX_DV   = r_RX_DV;
  assign o_RX_Byte = r_RX_Byte;

  //Control RX state machine
  always @(posedge i_Clock) begin
    case (r_SM_Main)

      IDLE: begin
        r_RX_DV       <= 1'b0;
        r_Clock_Count <= 0;
        r_Bit_Index   <= 0;

        if (i_RX_Serial == 1'b0)       //start bit found (line went low)
          r_SM_Main <= RX_START_BIT;
        else
          r_SM_Main <= IDLE;
      end

      //Check middle of start bit to ensure still low
      RX_START_BIT: begin
        if (r_Clock_Count == (CLKS_PER_BIT-1)/2) begin
          if (i_RX_Serial == 1'b0) begin
            r_Clock_Count <= 0;
            r_SM_Main     <= RX_DATA_BITS;
          end else begin
            //false start bit, go back to idle
            r_SM_Main <= IDLE;
          end
        end else begin
          r_Clock_Count <= r_Clock_Count + 1;
        end
      end

      //Wait CLKS_PER_BIT-1 clock cycles to sample serial data
      RX_DATA_BITS: begin
        if (r_Clock_Count < CLKS_PER_BIT-1) begin
          r_Clock_Count <= r_Clock_Count + 1;
        end else begin
          r_Clock_Count            <= 0;
          r_RX_Byte[r_Bit_Index]   <= i_RX_Serial;

          if (r_Bit_Index < 3'd7) begin
            r_Bit_Index <= r_Bit_Index + 1;
          end else begin
            r_Bit_Index <= 0;
            r_SM_Main   <= RX_STOP_BIT;
          end
        end
      end

      //Receive stop bit, stop bit = 1
      RX_STOP_BIT: begin
        if (r_Clock_Count < CLKS_PER_BIT-1) begin
          r_Clock_Count <= r_Clock_Count + 1;
        end else begin
          //One full stop bit elapsed
          r_Clock_Count <= 0;
          r_RX_DV       <= 1'b1;
          r_SM_Main     <= CLEANUP;
        end
      end

      CLEANUP: begin
        r_SM_Main <= IDLE;
        r_RX_DV   <= 1'b0;
      end

      default: r_SM_Main <= IDLE;
    endcase
  end

endmodule



