package ashwiniyer06.gmail.com;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLConnection;
import java.util.*;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Pattern;

import net.minecraft.block.Block;
import net.minecraft.client.Minecraft;
import net.minecraft.init.Blocks;
import net.minecraft.init.Items;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraftforge.client.ClientCommandHandler;
import net.minecraftforge.client.MinecraftForgeClient;
import net.minecraftforge.client.event.ClientChatReceivedEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.ServerChatEvent;
import net.minecraftforge.fml.client.FMLClientHandler;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.Mod.EventHandler;
import net.minecraftforge.fml.common.event.FMLInitializationEvent;
import net.minecraft.client.gui.inventory.GuiContainer;
import net.minecraft.inventory.Slot;
import net.minecraft.item.ItemStack;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

@Mod(modid = AHFlip.MODID, version = AHFlip.VERSION)
public class AHFlip {

    public static final String MODID = "FlipAH";
    public static final String VERSION = "1.0";


    @EventHandler
    public void init(FMLInitializationEvent event) {
        MinecraftForge.EVENT_BUS.register(this);
        ClientCommandHandler.instance.registerCommand(new FlipStart(this));
    }
    public static String getBestAuction() throws Exception {
        URL url = new URL("http://localhost:8080/");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();

        conn.setRequestMethod("GET");
        conn.setRequestProperty("Accept", "application/json");

        if (conn.getResponseCode() != 200) {
            throw new RuntimeException("Failed : HTTP error code : "
                    + conn.getResponseCode());
        }

        BufferedReader br = new BufferedReader(new InputStreamReader((conn.getInputStream())));

        String output;
        StringBuilder response = new StringBuilder();
        while ((output = br.readLine()) != null) {
            response.append(output);
        }

        conn.disconnect();
        return response.toString();
    }
    public void startFlipping(String uuid) {

        Minecraft.getMinecraft().thePlayer.sendChatMessage("/viewauction " + uuid);

        //Separate checkForGui into function and call it from another thread, so it does not block game.
        new Thread(() -> {
            try {
                checkForGui(uuid);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        }).start();
    }

    private void checkForGui(String uuid) throws InterruptedException {
        Thread.sleep(300);
            if (Minecraft.getMinecraft().currentScreen instanceof GuiContainer) {
                System.out.println("GUI IS OPEN");
                GuiContainer containerGUI = (GuiContainer) Minecraft.getMinecraft().currentScreen;

                for (Slot slot : containerGUI.inventorySlots.inventorySlots) {
                    ItemStack stack = slot.getStack();

                    if (stack != null) {
                        Item item = stack.getItem();

                        if (item == Items.bed) {
                            //Please check these item types per your minecraft version.
                            while (item == Items.bed) {
                                Minecraft.getMinecraft().playerController.windowClick(containerGUI.inventorySlots.windowId, slot.slotNumber, 0, 0, Minecraft.getMinecraft().thePlayer);
                                try {
                                    Thread.sleep(300);
                                } catch (InterruptedException e) {
                                    e.printStackTrace();
                                }
                                item = stack.getItem();
                            }
                            Minecraft.getMinecraft().playerController.windowClick(containerGUI.inventorySlots.windowId, slot.slotNumber, 0, 0, Minecraft.getMinecraft().thePlayer);
                        } else if (item == Items.gold_nugget) {
                            Minecraft.getMinecraft().playerController.windowClick(containerGUI.inventorySlots.windowId, slot.slotNumber, 0, 0, Minecraft.getMinecraft().thePlayer);
                            item = stack.getItem();
                            try {
                                Thread.sleep(150);
                            } catch (InterruptedException e) {
                                e.printStackTrace();
                            }

                            try {
                                Thread.sleep(50);
                                GuiContainer containerGUI2 = (GuiContainer) Minecraft.getMinecraft().currentScreen;
                                CheckSecondPage(containerGUI2);
                                if(checkGUI()){
                                    Minecraft.getMinecraft().thePlayer.closeScreen();
                                }
                                else{
                                    CheckSecondPage(containerGUI2);
                                }


                            } finally {
                                Thread.sleep(300);
                                System.out.println("it is so over");
                            }
                        } else if (item == Items.potato) {
                            Minecraft.getMinecraft().thePlayer.closeScreen();
                            Thread.sleep(300);
                            System.out.println("it is so over");
                        }
                    }
                }
            } else {
                if(Click){
                    boolean GUIOpen = checkGUI();
                    int count = 0;
                    while(!GUIOpen && count < 5){
                        count++;
                        Minecraft.getMinecraft().thePlayer.sendChatMessage("/viewauction " + uuid);
                        try {
                            // Sleep the thread for a moment, so we're not constantly checking - change value as necessary
                            Thread.sleep(150);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                        checkForGui(uuid);
                    }
                    Click = false;
                }
                if(checkGUI()){
                    Minecraft.getMinecraft().thePlayer.closeScreen();
                }

            }
        if(checkGUI()){
            Minecraft.getMinecraft().thePlayer.closeScreen();
        }
    }

    private void CheckSecondPage(GuiContainer containerGUI2) {
        for (Slot slot2 : containerGUI2.inventorySlots.inventorySlots) {
            ItemStack stack2 = slot2.getStack();
            if (stack2 != null) {
                Block block = Block.getBlockFromItem(stack2.getItem());
                System.out.println(block.toString() + " " + stack2.getMetadata());
                if (block == Blocks.stained_hardened_clay && stack2.getMetadata() == 13) { // for green block
                    // If slot2 id is less than half the total slots, it might be on the left hand side.
                    if (slot2.slotNumber < containerGUI2.inventorySlots.inventorySlots.size() / 2) {
                        Minecraft.getMinecraft().playerController.windowClick(containerGUI2.inventorySlots.windowId, slot2.slotNumber, 0, 0, Minecraft.getMinecraft().thePlayer);
                        break; // break out of the loop after clicking
                    }
                    try {
                        Thread.sleep(150);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }


                }
            }
        }
    }

    private boolean checkGUI(){
        return(Minecraft.getMinecraft().currentScreen instanceof GuiContainer);
    }
    boolean Click = false;
    @SubscribeEvent
    public void ValidAuction(ClientChatReceivedEvent event) {
        String message = event.message.getUnformattedText();

        if(message.contains("Wait")) {
            Click = true;
        }
        else if(message.contains("Invalid auction")){
            Click = false;
        }
        else if(message.contains("You don't have enough coins to afford")){
            Click = false;
        }
        else{
            Click = false;
        }
    }

}





